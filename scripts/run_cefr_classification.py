import os
import multiprocessing as mp
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from tqdm import tqdm

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

def process_chunk_on_gpu(gpu_id: int, df_chunk: pd.DataFrame, return_dict: dict):
    """
    각 GPU 독립 프로세스에서 실행되는 Qwen2.5 기반 CEFR 분류 추론 함수.
    """
    device = f"cuda:{gpu_id}"
    print(f"[GPU {gpu_id}] 프로세스 가동 완료. 처리할 문장 수: {len(df_chunk)}개")
    
    # 1. 공식 문서 스펙에 맞춘 토크나이저 및 모델 로드 및 GPU 할당
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(device)
    model.eval()  # 추론 모드 전환 (기울기 계산 비활성화 준비)
    
    # 2. 분석 타겟 영어 문장 추출
    sentences = df_chunk["번역문"].astype(str).tolist()
    
    cefr_labels = []
    confidence_scores = []
    
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
            for confidence, idx in zip(confidences.tolist(), pred_idxs.tolist()):
                cefr_labels.append(LABELS[idx])
                confidence_scores.append(confidence)
                
    except Exception as e:
        print(f"[GPU {gpu_id}] 추론 중 에러 발생: {e}")
        return

    # 4. 추론 결과를 기존 데이터프레임 청크에 매핑
    df_chunk["cefr_level"] = cefr_labels
    df_chunk["confidence_score"] = confidence_scores
    
    # 5. [데이터 클리닝] 신뢰도 점수가 Threshold(0.3) 이상인 정제 데이터만 필터링
    cleaned_chunk = df_chunk[df_chunk["confidence_score"] >= CONFIDENCE_THRESHOLD]
    dropped_count = len(df_chunk) - len(cleaned_chunk)
    print(f"[GPU {gpu_id}] 데이터 정제 완료. (유지: {len(cleaned_chunk)}개 / 제거: {dropped_count}개)")
    
    # 6. 결과 취합용 공유 딕셔너리에 저장
    return_dict[gpu_id] = cleaned_chunk


if __name__ == "__main__":
    # 멀티프로세스 시작 방식 설정 (CUDA 연산 안전성 확보)
    mp.set_start_method('spawn', force=True)
    
    num_gpus = torch.cuda.device_count()
    print(f"==================================================")
    print(f"🎯 VIPA 대규모 Qwen2.5 기반 데이터 정제 파이프라인 가동")
    print(f"▶ 사용 가능한 GPU 개수: {num_gpus}대")
    print(f"==================================================")

    # 1. AI 허브 로우 데이터셋 로드
    print(f"① 원본 엑셀 데이터셋 로드 중... ({INPUT_EXCEL_PATH})")
    # openpyxl을 통해 수동 변환 없이 엑셀 파일을 바로 파싱합니다.
    df = pd.read_excel(INPUT_EXCEL_PATH, engine="openpyxl")
    print(f"▶ 로드 완료. 총 문장 수: {len(df):,}개")

    # 2. Dual GPU 분산 처리를 위한 데이터 이등분
    chunks = np.array_split(df, 2)
    
    manager = mp.Manager()
    return_dict = manager.dict()
    processes = []

    # 3. 멀티 GPU 병렬 프로세스 생성 및 가동
    print(f"② 병렬 프로세서 기법 기반 분산 추론 시작 (A100 Dual GPU)")
    for i in range(2):
        p = mp.Process(target=process_chunk_on_gpu, args=(i, chunks[i], return_dict))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # 4. 분산 데이터 취합 및 최종 병합
    print(f"③ 각 GPU 세탁 데이터 취합 및 최종 병합 중...")
    final_df = pd.concat([return_dict[0], return_dict[1]], ignore_index=True)

    # 5. PostgreSQL 이식용 최종 CSV 저장
    # 폴더가 없을 경우 자동 생성
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    
    print(f"==================================================")
    print(f"🏆 금주 작업 데이터 세탁 파이프라인 최종 완료")
    print(f"▶ 원본 데이터 문장 수: {len(df):,} 개")
    print(f"▶ 최종 정제 완료 문장 수: {len(final_df):,} 개")
    print(f"▶ 필터링되어 유실된 저품질 문장 수: {len(df) - len(final_df):,} 개")
    print(f"▶ 저장 경로: {os.path.abspath(OUTPUT_CSV_PATH)}")
    print(f"==================================================")