import os
import multiprocessing as mp
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from tqdm import tqdm
import string

# ==========================================
# [설정 항목] 프로젝트 경로 및 파라미터 정의
# ==========================================
INPUT_EXCEL_PATH = "../data/raw/1_구어체(2)_200226.xlsx"  # 원본 데이터셋 경로 (Excel 포맷)
OUTPUT_CSV_PATH = "../data/processed/vipa_cefr_cleaned_dataset.csv"  # 최종 정제된 데이터셋 저장 경로
MODEL_NAME = "yanou16/cefr-english-classifier"          # 사용할 허깅페이스 CEFR 분류 모델
BATCH_SIZE = 128       # Qwen2.5-1.5B 모델 크기를 고려하여 A100 환경에 최적화된 대형 배치 설정
CONFIDENCE_THRESHOLD = 0.3  # 교수님 보고용 데이터 클리닝 기준 점수 (0.3 미만 필터링)

# 모델 공식 스펙에 명시된 CEFR 레이블 매핑 구조
LABELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# 🌟 [추가] 변별력 없는 기초 영어 단어(불용어) 제외 리스트 -> target_word 오염 방지용
STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "he", "him", "his", "she", "her", "it", "its", "they", "them", "their", "what", "which", 
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", 
    "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", 
    "with", "about", "against", "between", "into", "through", "during", "before", "after", 
    "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", 
    "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", 
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", 
    "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
}

def extract_target_word(sentence: str) -> str:
    """
    🌟 [기능 위젯] 영어 문장에서 조사/대명사를 제거하고 가장 긴 핵심 학습 단어를 추출합니다.
    """
    if not isinstance(sentence, str) or not sentence.strip():
        return "word"
    
    # 문장부호 제거 및 소문자 전처리
    clean_sentence = sentence.translate(str.maketrans('', '', string.punctuation))
    words = clean_sentence.lower().split()
    
    # 불용어를 배제하고 실질적인 의미가 있는 어휘 후보 추출 (3글자 이상)
    meaningful_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    
    # 알짜배기 단어가 없다면 전체 중 최장 단어 선택, 그마저도 없다면 기본 fallback 단어 지정
    if not meaningful_words:
        return max(words, key=len) if words else "vocabulary"
    
    # 변별력이 높은 가장 긴 단어를 핵심 단어(target_word)로 반환
    return max(meaningful_words, key=len)


def process_chunk_on_gpu(gpu_id: int, df_chunk: pd.DataFrame, return_dict: dict):
    """
    각 GPU 독립 프로세스에서 실행되는 Qwen2.5 기반 CEFR 분류 추론 및 정제 함수.
    """
    device = f"cuda:{gpu_id}"
    print(f"[GPU {gpu_id}] 프로세스 가동 완료. 처리할 문장 수: {len(df_chunk):,}개")
    
    # 1. 공식 문서 스펙에 맞춘 토크나이저 및 모델 로드 및 GPU 할당
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(device)
    model.eval()  # 추론 모드 전환 (기울기 계산 비활성화 준비)
    
    # 🚨 [수정] 영어 분류 모델이므로 '번역문'이 아닌 '영어 원문'을 정밀 분석 타겟으로 추출합니다.
    sentences = df_chunk["원문"].astype(str).tolist()
    
    cefr_labels = []
    confidence_scores = []
    target_words = []
    
    # 3. 배치를 직접 쪼개어 대용량 GPU 연산 수행 (OOM 방지 및 속도 극대화)
    try:
        for i in tqdm(range(0, len(sentences), BATCH_SIZE), desc=f"GPU {gpu_id} Inference"):
            batch = sentences[i:i + BATCH_SIZE]
            
            # 공식 문서 가이드: max_length=256 및 truncation 필수 적용
            inputs = tokenizer(
                batch, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=256
            ).to(device)
            
            with torch.no_grad():
                logits = model(**inputs).logits
                
            # Softmax 연산을 통해 각 레벨별 확률 분포 계산
            probs = F.softmax(logits, dim=-1)
            
            # 가장 확률이 높은 레이블의 인덱스와 확률값(Confidence) 추출
            confidences, pred_idxs = torch.max(probs, dim=-1)
            
            # 결과 배열 변환 및 저장
            for confidence, idx, text in zip(confidences.tolist(), pred_idxs.tolist(), batch):
                cefr_labels.append(LABELS[idx])
                confidence_scores.append(confidence)
                # 🌟 [추가] 추론과 동시에 예문에서 핵심 단어를 실시간 파싱하여 병렬 적재
                target_words.append(extract_target_word(text))
                
    except Exception as e:
        print(f"[GPU {gpu_id}] 추론 중 에러 발생: {e}")
        return

    # 🌟 [수정] DB의 실제 테이블 컬럼명과 완전 일치하도록 데이터 프레임 뼈대를 조립합니다.
    df_chunk["target_word"] = target_words
    df_chunk["cefr_level"] = cefr_labels
    df_chunk["expression"] = df_chunk["원문"]
    df_chunk["meaning"] = df_chunk["번역문"]
    df_chunk["confidence_score"] = confidence_scores # 필터링 조건 비교를 위한 임시 컬럼 생성
    
    # 5. [데이터 클리닝] 신뢰도 점수가 Threshold(0.3) 이상인 정제 데이터만 필터링
    cleaned_chunk = df_chunk[df_chunk["confidence_score"] >= CONFIDENCE_THRESHOLD]
    
    # 🚨 DB 이식 전용 구조 변환: DB 엔티티에 존재하지 않는 불필요 잔여 컬럼(신뢰도 등) 청소
    cleaned_chunk = cleaned_chunk[["target_word", "cefr_level", "expression", "meaning"]]
    
    dropped_count = len(df_chunk) - len(cleaned_chunk)
    print(f"[GPU {gpu_id}] 데이터 정제 완료. (유지: {len(cleaned_chunk):,}개 / 제거: {dropped_count}:,개)")
    
    # 6. 결과 취합용 공유 딕셔너리에 저장
    return_dict[gpu_id] = cleaned_chunk


if __name__ == "__main__":
    # CUDA 다중 프로세스 메모리 충돌 방지를 위한 최우선 컨텍스트 설정
    mp.set_start_method('spawn', force=True)
    
    num_gpus = torch.cuda.device_count()
    print(f"==================================================")
    print(f"🎯 VIPA 대규모 Qwen2.5 기반 데이터 정제 파이프라인 가동")
    print(f"▶ 사용 가능한 GPU 개수: {num_gpus}대")
    print(f"==================================================")

    if num_gpus == 0:
        print("❌ 에러: 가용 가능한 GPU 연산 디바이스가 없습니다.")
        exit(1)

    # 🌟 [선행 공정 추가]: 멀티프로세스 충돌 방지를 위해 메인에서 모델을 먼저 안전하게 다운로드합니다.
    print(f"① 허깅페이스로부터 [{MODEL_NAME}] 모델 및 토크나이저 사전 다운로드 중...")
    try:
        AutoTokenizer.from_pretrained(MODEL_NAME)
        AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        print("▶ 모델 다운로드 및 캐싱 완료! 안전하게 병렬 공정을 전개합니다.")
    except Exception as e:
        print(f"❌ 모델 사전 다운로드 실패 (인터넷/미러 서버 확인 필요): {e}")
        exit(1)

    # 2. AI 허브 로우 데이터셋 로드
    print(f"② 원본 엑셀 데이터셋 로드 중... ({INPUT_EXCEL_PATH})")
    df = pd.read_excel(INPUT_EXCEL_PATH, engine="openpyxl")
    print(f"▶ 로드 완료. 총 문장 수: {len(df):,}개")

    # 3. 자원 낭비 방지를 위해 가용 GPU 개수만큼 균등 분산 이등분 실행
    print(f"③ 분산 처리를 위한 데이터 분할 공정 가동 (균등 {num_gpus}등분)")
    chunks = np.array_split(df, num_gpus)
    
    manager = mp.Manager()
    return_dict = manager.dict()
    processes = []

    # 4. 멀티 GPU 병렬 프로세스 생성 및 가동
    print(f"④ 병렬 프로세서 기법 기반 분산 추론 시작 (A100 가속화 공정)")
    for i in range(num_gpus):
        p = mp.Process(target=process_chunk_on_gpu, args=(i, chunks[i], return_dict))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # 5. 취합 및 동적 최종 결합 수행
    print(f"⑤ 각 GPU 세탁 데이터 취합 및 최종 병합 중...")
    final_df = pd.concat([return_dict[i] for i in range(num_gpus)], ignore_index=True)

    # 6. PostgreSQL 이식용 최종 CSV 저장
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    
    print(f"==================================================")
    print(f"🏆 금주 작업 데이터 세탁 파이프라인 최종 완료")
    print(f"▶ 원본 데이터 문장 수: {len(df):,} 개")
    print(f"▶ 최종 정제 완료 문장 수: {len(final_df):,} 개")
    print(f"▶ 필터링되어 유실된 저품질 문장 수: {len(df) - len(final_df):,} 개")
    print(f"▶ 저장 경로: {os.path.abspath(OUTPUT_CSV_PATH)}")
    print(f"==================================================")