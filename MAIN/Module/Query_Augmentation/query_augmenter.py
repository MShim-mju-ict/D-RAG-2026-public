from MAIN.Connection.llm_conn import get_gpt_client
import json

llm = get_gpt_client()

def augment_query1(user_input, logs=True):
    if logs: print("augment_query 1 @work")
    """
    OpenAI를 호출하여 공공데이터 메타데이터를 생성하고 문자열 결과만 반환합니다.
    """

    SYSTEM_PROMPT = """너는 "공공데이터 포털의 검색 도우미" 역할을 수행한다.

목표:
사용자가 제공한 키워드들을 기반으로, 공공데이터 포털에서 실제로 검색될 가능성이 높은, 의미적으로 유사하지만 표현, 어감, 용도가 다른 키워드들을 추가한다.

입력 텍스트의 각 줄바꿈(개행)은 데이터 구조의 일부이다.
각 입력 줄은 하나의 독립된 레코드이며,
출력에서도 동일한 줄바꿈 위치를 반드시 유지해야 한다.

중요 규칙:
1. 단순 문자열 포함(substring)이나 형태 변화(조사, 접미사 추가)는 제외한다.
2. 반드시 의미적으로 동등하거나 매우 유사한 단어만 생성한다.
3. 공공데이터 포털, 행정 문서, 정책 자료, 통계, 법·제도 문맥에서 실제로 사용될 수 있는 표현만 사용한다.
4. 일상어보다는 행정·공공·정책적 표현을 우선한다.
5. 추상적인 연상어, 설명 문장, 해석은 포함하지 않는다.
6. 각 키워드는 독립적으로 판단하여 증강한다.
7. 키워드 마다 4 이상의 증강을 한다.

출력 형식 규칙 (매우 중요):
1. 입력 키워드 1줄당 출력도 반드시 1줄로 한다.
2. 각 출력 줄의 첫 번째 항목은 반드시 원본 키워드여야 한다.
3. 이후 항목들은 원본 키워드의 의미 기반 증강 키워드들이다.
4. 모든 항목은 쉼표(,)로 구분한다.
5. 불필요한 설명, 번호, 공백 줄, 기호는 출력하지 않는다.
6. 모든 결과를 한 줄로 합치지 마라.
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

    return "".join(text_chunks).strip() or str(resp)


def augment_query2(user_input: str, logs: bool = True) -> str:
    """
    OpenAI JSON 모드를 호출하여 공공데이터 검색용 질의를 증강하고,
    입력된 줄바꿈 구조를 유지한 단일 문자열로 반환합니다.
    """
    if logs:
        print("augment_query 1 @work")

    SYSTEM_PROMPT = """[System Role]
당신은 공공데이터 포털 질의 증강(Query Augmentation) 모델입니다. 
사용자가 입력한 일상적인 검색어를 바탕으로, 실제 공공데이터 포털의 메타데이터(행정 문서, 법령, 정책 통계 등)에서 사용될 확률이 높은 공식 용어로 확장하는 역할을 수행합니다.

[Rules]
1. 행정/공식 용어 매핑: 사용자의 일상어(구어체)를 의미적으로 동일한 행정·공공·정책적 표현(문어체)으로 변환 및 추가하세요.
2. 각 키워드별 독립적 증강: 입력된 개별 키워드의 의미를 훼손하지 않는 선에서, 동의어, 유의어, 법적/제도적 명칭을 키워드당 최소 4개 이상 생성하세요.
3. 형태소 변형 금지: 단순 조사/접미사 변경은 배제하고, 실질적인 의미가 담긴 명사형 키워드만 생성하세요.
4. 원본 포함: 출력되는 각 키워드의 배열 첫 번째 값은 반드시 사용자가 입력한 '원본 키워드'여야 합니다.

[Output Format]
반드시 입력된 원본 키워드를 Key로, 증강된 키워드 배열을 Value로 가지는 유효한 JSON 객체만 출력하세요. 
"""

    try:
        response = llm.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"다음 키워드 목록을 줄 단위로 분리하여 분석하고 증강하세요:\n{user_input}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.3,  # 질의 증강은 메타데이터 증강보다 엄격해야 하므로 창의성을 약간 낮춤
        )

        # LLM 응답을 딕셔너리로 완벽하게 파싱
        augmented_data = json.loads(response.choices[0].message.content)

        # 딕셔너리 값들을 꺼내어 (1줄당 1키워드 세트) 요구된 문자열 형태로 조립
        output_lines = []
        for original_kw, expanded_list in augmented_data.items():
            # 리스트를 쉼표(,)로 연결하여 한 줄로 만듦
            line_str = ", ".join(expanded_list)
            output_lines.append(line_str)

        # 조립된 줄들을 개행(\n)으로 연결하여 반환
        return "\n".join(output_lines)

    except Exception as e:
        if logs:
            print(f"Error during query augmentation: {e}")
        return ""  # 장애 발생 시 원본이라도 살려서 검색 엔진으로 넘기기 위한 Fallback
