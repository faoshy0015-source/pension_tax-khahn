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


## 2026-10-19 UI visibility update
- Retuned the dark theme for high contrast: Hana green emphasis, bright labels and values, distinguishable input borders, and improved table/metric readability.
- `.streamlit/config.toml` supplies the native theme; `app.py` also includes the required CSS so replacing just `app.py` improves contrast on an already deployed app.
- Only presentation was changed. No retirement tax calculation formulas or input behavior were changed.
- To upload the theme file through GitHub's web interface, preserve its path as `.streamlit/config.toml`.

## 2026-10-19 UI V3 — 화면 캡처 반영
- 4열 `st.metric()`의 `...` 잘림 현상 제거: 큰 숫자는 만/억 단위로 크게 표시하고 **정확한 원화 금액도 함께 표기**합니다.
- KPI 제목이 말줄임표로 잘리지 않고 여러 줄로 표시되도록 변경했습니다.
- 날짜 위젯의 밝은 외부 배경과 흰 내부 글씨가 겹치던 문제를 방지하도록 입력창 래퍼까지 진한 색으로 고정했습니다.
- 입력창, 드롭다운, 버튼, 체크박스, 테이블의 다크/하나그린 테마 일관성을 강화했습니다.
- 세법 계산 코드 `retirement_core.py`는 변경하지 않았습니다. `test_core.py`의 계산 테스트 8개 통과.

### GitHub 배포
가장 쉬운 방법은 GitHub 기존 저장소의 `app.py`를 이 파일로 교체하여 커밋하는 것입니다.
입력 UI 외에 내장 Streamlit 테마까지 변경하려면 `.streamlit/config.toml`도 함께 올려 주세요.
