# HanaV Pension Tax Lab (시험용 2026)

## 실행
Windows PowerShell에서 이 폴더로 이동해 다음을 실행합니다.

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Streamlit Cloud에서는 이 폴더 파일을 GitHub 리포지토리로 업로드하고 `app.py`를 메인으로 지정하세요.

## 계산 범위
- 2026년 국세청 기준 근속연수공제/환산급여공제/퇴직소득세 계산 (단순 근속·비과세 가정)
- 2013-03-01 이전 연금계좌 가입 및 이전 DB형 가입자의 전액 신규 IRP 이전 경과특례
- 연금수령한도 계산 연차와 연금 실제수령연차 **별도 관리**
- 수령한도 내/외 인출금액 자동 분리, 인출순서(과세제외 → 이연퇴직 → 세액공제분·운용수익)
- 잔여 이연퇴직소득세 원본 입력 또는 추정세액, 지방소득세
- 2026년 실제수령연차 1~10년 70%, 11~20년 60%, 21년 이상 50%
- 세액공제분·운용수익은 연령별 연금소득세 또는 연금외수령 기타소득세율 적용
- CSV 다운로드

## 주의
**내부 상담용 검산 MVP일 뿐, 실제 원천징수용 프로그램 아님.**
반드시 해당 고객의 퇴직소득 원천징수영수증, 연금계좌 세액원장, 수령연차 기록과 대조하세요.
퇴직금 중간정산, 근속 제외기간, 임원 한도, 계좌 간 이전/승계, 재원별 운용수익 원가 배분, 다수 퇴직소득세 이연 원장, 사적연금 과세 특례 및 종합과세는 별도 고도화 필요.

## 공식 자료
- https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7880&mi=6444
- https://webtv.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6452
- https://www.law.go.kr/lumLsLinkPop.do?chrClsCd=010202&lspttninfSeq=126416
