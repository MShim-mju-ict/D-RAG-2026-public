from MAIN.Connection.llm_conn import get_gpt_client
import json

def result_aug1(user_query, search_result, logs=True):
    if logs: print("result aug 1 @work")
    llm = get_gpt_client()

    user_input = f"user query:\n{user_query}\nsearch result:\n{search_result}"


    SYSTEM_PROMPT = """너는 공공데이터 포털에서 검색된 여러 데이터셋 중, 사용자의 질문에 가장 적합한 데이터셋을 선별하고 우선순위를 정해 추천하는 AI 어시스턴트야.

입력으로는 사용자의 자연어 질문(query)과, 검색된 각 데이터셋의 메타데이터(metadata) 및 열 이름(column names)이 주어질 거야.

다음 작업을 수행해줘:

각 데이터셋이 사용자의 질문에 적합한지 판단해.

출력 형식은 다음과 같아:

각 데이터셋은 한 단락으로 표현해.

구성은: ID, 데이터셋 이름, 한 줄 설명 (왜 이 데이터셋이 사용자 질문과 관련이 있는지 설명해줘).

ID: 000 Name:000 expl:000

관련 없는 데이터셋은 포함하지 않아도 돼.
관련 있는 데이터셋은 다 포함해 꼭 2-3만 할 필요는 없어.
무조건 우선순위대로 정렬을 하여야 돼


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


def result_aug2(user_query: str, search_result: str, logs: bool = True) -> str:
    """
    OpenAI JSON 모드를 호출하여 검색 결과를 재정렬(Re-ranking) 및 필터링하고,
    정해진 문자열 포맷(ID, Name, expl)으로 조립하여 반환합니다.
    """
    client = get_gpt_client()
    if logs:
        print("result_aug1 @work")

    user_input = f"User Query:\n{user_query}\n\nCandidate Search Results:\n{search_result}"

    SYSTEM_PROMPT = """[System Role]
당신은 공공데이터 포털의 '검색 결과 재정렬 및 검증(Re-ranking & Verification)'을 수행하는 심사관(Relevance Judge)입니다.
사용자의 자연어 질문(Query) 의도와 검색된 후보 데이터셋들의 메타데이터(설명, 컬럼명 등)를 의미론적으로 비교하여, 가장 적합한 데이터셋을 선별하고 우선순위대로 정렬합니다.

[Rules]
1. 관련성 검증 (필터링): 검색된 데이터셋 중 사용자의 질문 의도를 해결하는 데 실질적인 도움이 되지 않는 데이터셋은 과감히 제외하세요. 모든 결과를 포함할 필요는 없습니다.
2. 우선순위 정렬 (Re-ranking): 사용자 질문에 가장 완벽하게 부합하는 데이터셋부터 내림차순으로 엄격하게 정렬하세요.
3. 근거 기반 설명 (Grounded Justification): 각 데이터셋이 왜 관련이 있는지 한 줄로 설명할 때, 상상하지 말고 반드시 '제공된 데이터셋의 메타데이터와 컬럼'에 근거하여 작성하세요.

[Output Format]
반드시 'ranked_results'라는 단일 키를 가지고, 아래 형식의 객체 배열을 값으로 가지는 유효한 JSON 객체만 반환하세요.
{
  "ranked_results": [
    {
      "id": "문자열 (데이터셋 ID)",
      "name": "문자열 (데이터셋 이름)",
      "explanation": "문자열 (관련된 이유 한 줄 설명)"
    }
  ]
}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
            temperature=0.1,  # 심사(Judge) 역할이므로 환각을 없애고 가장 이성적인 판단을 내리도록 매우 낮게 설정
        )

        # LLM 응답 파싱
        response_dict = json.loads(response.choices[0].message.content)
        ranked_items = response_dict.get("ranked_results", [])

        # 이전 코드와의 호환성을 위해 요구된 텍스트 포맷으로 조립
        output_lines = []
        for item in ranked_items:
            # 혹시 모를 키(Key) 에러 방지를 위해 .get() 활용
            ds_id = item.get("id", "Unknown")
            ds_name = item.get("name", "Unknown")
            ds_expl = item.get("explanation", "설명 없음")

            line = f"ID: {ds_id} Name: {ds_name} expl: {ds_expl}"
            output_lines.append(line)

        return "\n".join(output_lines)

    except Exception as e:
        if logs:
            print(f"Error during result augmentation (re-ranking): {e}")
        # 오류 발생 시 원본 검색 결과를 그대로 반환하여 파이프라인 단절 방지
        return ""
