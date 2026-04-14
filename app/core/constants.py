# app/core/constants.py
# 비트 마스크 상수로 관리
SOCIAL_NONE = 0 # 소셜 로그인 안 함 (비트: 0000)
SOCIAL_GOOGLE = 1  # 2^0 (비트: 0001)
SOCIAL_KAKAO = 2   # 2^1 (비트: 0010)
# 추후 APPLE = 4, NAVER = 8 등으로 확장 가능