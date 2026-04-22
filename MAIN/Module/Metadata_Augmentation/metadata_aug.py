# This file is responsible for augmenting metadata of documents or datasets.
# This could involve extracting additional keywords, classifying content, etc.
from MAIN.Connection.llm_conn import get_gpt_client
import json

llm = get_gpt_client()

def augment_metadata1(user_input):
    print("augment_metadata 1 @work")
    """
    OpenAI를 호출하여 공공데이터 메타데이터를 생성하고 문자열 결과만 반환합니다.
    """

    SYSTEM_PROMPT = """역할: 너는 공공데이터 포털의 메타데이터 전문가다. 현재 너의 업무는 각 데이터셋의 기존 메타데이터(제목, 설명, 기존 키워드)기반으로 검색 최적화용 메타데이터를 생성하는 것이다.

목표: 주어진 입력을 바탕으로, 다음 두 가지를 생성하라.
1. "keywords": 이 데이터셋을 설명하는 키워드 목록 (한글 기준)
2. "search_index": 각 키워드를 유사어, 동의어, 관련 개념 등으로 확장한 검색용 인덱스 키워드 목록 (한글 기준) (유일한 출력물)

작업 지침:
[1] 시간 관련 키워드 생성 규칙: 데이터셋이 포함하는 연도를 나열하고, 시간 단위를 "*별" 형식으로 포함한다.
[2] 공간 관련 키워드 생성 규칙: 지리적 위치 및 제공 기관 위치를 포함하며, 공간 단위를 "**별" 형식으로 추출한다.
[3] 일반 키워드 생성 규칙: 기존 메타데이터와 컬럼명을 분석하여 다양한 주제 키워드를 도출한다.
[4] search_index 생성 규칙: 생성한 키워드를 기반으로  각 keyword 마다 4-5 정도로. substring보다는 유사어/동의어를 최대한 많이 확장한다.

출력 형식: plain text list of search_index, 숫자나 기준 형식 없이 단어들만 쉼표로 구분하여서. keywords:, search_index:, [] {} 같은 구분 금지
"""

    # OpenAI API 호출 (사용자 제공 형식 유지)
    resp = llm.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_input}],
            },
        ],
    )

    # 응답에서 텍스트만 추출하여 문자열로 반환
    text_chunks = []
    for item in getattr(resp, "output", []) or []:
        for c in getattr(item, "content", []) or []:
            if getattr(c, "type", None) in ("output_text", "text"):
                text_chunks.append(getattr(c, "text", ""))

    return "\n".join([t for t in text_chunks if t.strip()]) or str(resp)

def augment_metadata2(user_input):
    print("augment_metadata 2 @work")
    """
    OpenAI를 호출하여 공공데이터 메타데이터를 생성하고 문자열 결과만 반환합니다.
    """

    SYSTEM_PROMPT = """
    [System Role]
당신은 공공데이터 검색 엔진 최적화(SEO) 및 메타데이터 증강 전문가입니다. 당신의 목표는 제공된 데이터셋의 메타데이터를 분석하여, 딱딱한 행정 용어와 일반 사용자의 일상적인 검색어 사이의 간극을 메워주는 확장된 검색 키워드 목록을 생성하는 것입니다. 생성되는 키워드의 기본 언어는 반드시 '한국어'여야 합니다 (단, 널리 쓰이는 영문 약어는 예외적으로 허용).

[Rules]
1. 상위 행정 용어의 하위/생활 용어 세분화 (가장 중요)
   - 포괄적이고 경직된 행정·산업 분류(상위어/문어체)를 일반 대중이 실제로 검색창에 입력할 법한 구체적인 개별 영업 형태 및 실생활 서비스(하위어/구어체)로 완벽히 풀어서 확장하세요.
   - 예시: "공중위생업" ➔ "세탁업", "숙박", "미용", "목욕장업"
   - 예시: "여객운수업" ➔ "시내버스", "택시", "고속버스", "지하철"

2. 동의어, 유사 개념 및 약어의 '최대치' 확장 (Exhaustive Generation)
   - 모델이 판단하기에 적당한 선에서 멈추지 마세요. 재현율(Recall) 극대화를 위해, 떠오르는 모든 유효한 연관어, 동의어, 하위 개념을 '가능한 한 무한대로(최소 핵심 단어당 5~10개 이상)' 폭넓게 도출해야 합니다.
   - 고유명사뿐만 아니라, 데이터의 속성이나 지표를 나타내는 일반 명사(예: "사망률")에 대해서도 대중이 혼용할 수 있는 유사 개념(예: "치명률", "이환율", "사망비율" 등)을 남김없이 브레인스토밍하여 포함하세요.

3. 의미 단위 띄어쓰기 (형태소 분리)
   - 검색 엔진의 토큰 인식률을 높이기 위해, 길게 붙어있는 복합명사는 독립적인 의미를 가지는 최소 단어 단위로 분리하여(띄어쓰기) 제시하세요.
   - 예시: "서울보건정책데이터" ➔ "서울", "보건", "정책", "데이터" (각각 개별 키워드로 분리)

4. 원본 배제 및 중복 제거
   - 생성된 모든 키워드는 고유해야 하며, 의미상 완전히 동일한 단어를 반복 나열하지 마세요.
   - 특히, 프롬프트로 이미 제공된 원본 메타데이터(Title, Description, Keywords)에 그대로 존재하는 단어는 새로운 확장 리스트에 중복해서 포함하지 마세요.

[Output Format]
인사말, 설명, 마크다운 코드 블록(```json 등)을 포함한 그 어떤 텍스트도 덧붙이지 마세요. 
오직 'keywords'라는 단일 키(key)를 가지고, 생성된 키워드 배열을 값(value)으로 가지는 유효한 JSON 객체(Object)만 출력해야 합니다.
예시 포맷: 
{
  "keywords": ["키워드1", "키워드2", "키워드3"]
}
"""
    # OpenAI API 호출 (사용자 제공 형식 유지)
    try:
        response = llm.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"다음 데이터셋 메타데이터를 분석하고, 시스템 규칙에 따라 최적화된 검색 키워드를 생성하세요.\n\n[Raw Metadata]\n{user_input}"}
            ],
            # 핵심: 모델이 반드시 JSON 객체 형태로만 답변하도록 강제
            response_format={"type": "json_object"},

            # 증강(Augmentation) 파라미터
            max_tokens=1000,
            temperature=0.5,
            presence_penalty=0.5
        )

        # 1. LLM으로부터 JSON 형태의 텍스트 응답 받기
        raw_json_str = response.choices[0].message.content

        # 2. 파이썬 딕셔너리로 파싱 후, 리스트만 추출
        parsed_data = json.loads(raw_json_str)
        keywords_list = parsed_data.get("keywords", [])

        # 3. 리스트를 쉼표(,)로 구분된 단일 문자열로 변환 (JSON -> String)
        keywords_string = ", ".join(keywords_list)

        return keywords_string

    except Exception as e:
        print(f"API 호출 또는 파싱 중 에러 발생: {e}")
        return ""