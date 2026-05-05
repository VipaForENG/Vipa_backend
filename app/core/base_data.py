from sqlalchemy.orm import Session
from app.models.category import MainCategory, SubCategory
from app.core.database import SessionLocal

def info_seed_data(db: Session):
    # 1. 기획안(image_b8295a.png) 기반 8대 카테고리 데이터
    categories_data = {
        "공항": [
            {"sub_title": "출입국 심사", "ai_role": "You are an immigration officer..."},
            {"sub_title": "수하물 분실", "ai_role": "You are an airport staff..."}
        ],
        "은행": [{"sub_title": "계좌 개설", "ai_role": "You are a bank teller..."}],
        "병원": [{"sub_title": "진료 접수", "ai_role": "You are a hospital receptionist..."}],
        "학교": [{"sub_title": "수강 신청", "ai_role": "You are a school staff..."}],
        "백화점": [{"sub_title": "환불 요청", "ai_role": "You are a clerk..."}],
        "회사": [{"sub_title": "프로젝트 회의", "ai_role": "You are a PM..."}],
        "마트": [{"sub_title": "물건 찾기", "ai_role": "You are a staff..."}],
        "그 외": [{"sub_title": "카페 주문", "ai_role": "You are a barista..."}]
    }

    # 2. 중복 방지 적재 로직 (멱등성 확보)
    for main_title, subs in categories_data.items():
        # [핵심] 메인 카테고리가 이미 존재하는지 확인
        main_cat = db.query(MainCategory).filter(MainCategory.title == main_title).first()
        
        if not main_cat:
            main_cat = MainCategory(title=main_title)
            db.add(main_cat)
            db.commit() # ID 생성을 위해 커밋
            db.refresh(main_cat)
            print(f"✅ 새 메인 카테고리 추가: {main_title}")
        else:
            # 이미 존재하면 로그만 남기고 다음 단계로 진행
            print(f"ℹ️ 기존 메인 카테고리 발견: {main_title} (ID: {main_cat.main_cat_id})")

        # 서브 카테고리 체크
        for sub in subs:
            sub_exists = db.query(SubCategory).filter(
                SubCategory.sub_title == sub["sub_title"],
                SubCategory.main_cat_id == main_cat.main_cat_id
            ).first()

            if not sub_exists:
                new_sub = SubCategory(
                    main_cat_id=main_cat.main_cat_id,
                    sub_title=sub["sub_title"],
                    ai_role=sub["ai_role"]
                )
                db.add(new_sub)
                print(f"   ㄴ ✅ 새 서브 카테고리 추가: {sub['sub_title']}")
    
    db.commit()

def init_db():
    db = SessionLocal()
    try:
        info_seed_data(db)
    finally:
        db.close()