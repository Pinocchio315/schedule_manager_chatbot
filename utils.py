import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

# 구글 캘린더 API 인증
def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
             return None
    return creds

def format_datetime(input_time):
    from datetime import datetime
    """
    ISO 8601 형식의 문자열을 '12월 29일 오후 3시' 또는 '12월 29일 오후 3시 30분' 형태로 변환합니다.
    
    Parameters:
    input_time (str): ISO 8601 형태의 시간 문자열 (예: 2024-12-29T15:00:00+09:00).
    
    Returns:
    str: 변환된 시간 문자열.
    """
    try:
        # 문자열을 datetime 객체로 변환 (타임존 정보 포함)
        dt = datetime.strptime(input_time, "%Y-%m-%dT%H:%M:%S%z")

        # 오전/오후 결정 및 12시간제로 시간 변환
        period = "오전" if dt.hour < 12 else "오후"
        hour = dt.hour if dt.hour <= 12 else dt.hour - 12
        hour = 12 if hour == 0 else hour  # 0시는 12시로 표시

        # 분 포함 여부 결정
        if dt.minute == 0:
            formatted_time = f"{dt.month}월 {dt.day}일 {period} {hour}시"
        else:
            formatted_time = f"{dt.month}월 {dt.day}일 {period} {hour}시 {dt.minute}분"

        return formatted_time

    except ValueError as e:
        # 입력 포맷이 예상과 다를 경우 예외 처리
        raise ValueError(f"잘못된 시간 형식: {input_time}. 오류: {e}")

# 구글 캘린더 일정 조회
def get_calendar_events(timeMin, timeMax):
    creds = get_credentials()
    if not creds:
        return "Google Calendar 인증에 실패했습니다. 'get_credentials.py'를 실행하여 인증을 완료해주세요."

    try:
        service = build('calendar', 'v3', credentials=creds)
        events_result = service.events().list(calendarId='primary', timeMin=timeMin,
                                            timeMax=timeMax, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            return "일정이 없습니다."
        else:
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_list.append(f"{format_datetime(start)} : {event['summary']}")
            event_result = "\n\n".join(event_list)
            return event_result
    except HttpError as error:
        return f"오류 발생: {error}"


def add_calendar_event(summary, start_time, end_time):
    """Google Calendar API를 사용하여 일정 추가"""
    creds = get_credentials()
    if not creds:
         return "Google Calendar 인증에 실패했습니다. 'get_credentials.py'를 실행하여 인증을 완료해주세요."

    try:
        service = build('calendar', 'v3', credentials=creds)
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Seoul',
            },
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"일정이 추가되었습니다."
    except HttpError as error:
        return f"오류 발생: {error}"





def delete_calendar_event(start_time):
    """
    Google Calendar API를 사용하여 시작 시간을 기준으로 모든 캘린더에서 일정을 검색하여 삭제합니다.
    입력받은 시간 문자열 뒤에 +09:00을 붙여 KST 시간대로 처리합니다.
    """
    creds = get_credentials()
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        start_time_dt = datetime.datetime.fromisoformat(start_time)
        timeMin = (start_time_dt - datetime.timedelta(minutes=1)).isoformat()
        timeMax = (start_time_dt + datetime.timedelta(minutes=1)).isoformat()

        timeMin = datetime.datetime.fromisoformat(timeMin).isoformat() + '+09:00'
        timeMax = datetime.datetime.fromisoformat(timeMax).isoformat() + '+09:00'

        service = build('calendar', 'v3', credentials=creds)
        events_result = service.events().list(calendarId='primary', timeMin=timeMin,
                                            timeMax=timeMax, singleEvents=True,
                                            orderBy='startTime').execute()

        events = events_result.get('items', [])
        start_time_dt = start_time_dt.fromisoformat(timeMin).isoformat() + '+09:00'
        if events:
            # 찾은 일정을 삭제
            for event in events:
                event_id = event['id']
                service.events().delete(calendarId='primary', eventId=event_id).execute()
                return f"캘린더에서 일정 ({event['summary']})을 삭제했습니다."
        else:
            return "해당 일정이 존재하지 않습니다."

    except HttpError as error:
        return f"에러 발생: {error}"

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def generate_response(prompt):
    """OpenAI API를 사용하여 챗봇 응답 생성"""
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 사용자의 일정을 관리해주는 챗봇입니다. 사용자에게 친절하고 정확하게 답변하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
         return f"오류 발생: {e}"

# 사용자의 입력으로부터 사용자의 의도를 파악하고 필요한 정보 추출
import datetime
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_openai import ChatOpenAI

def present_time():
    today = datetime.date.today()
    weekday = today.weekday()
    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    today_weekday = days[weekday]
    return today, today_weekday

llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
response_schemas = [
    ResponseSchema(name="intent", description="사용자의 의도를 분류합니다. '일정 추가', '일정 조회', '일정 삭제', '기타' 중 하나입니다."),
    ResponseSchema(name="summary", description="일정 제목입니다. 일정이 없으면 null입니다."),
    ResponseSchema(name="start_time", description="일정 시작 시간입니다. ISO 포맷으로 표현하고, 없으면 null입니다."),
    ResponseSchema(name="end_time", description="일정 종료 시간입니다. ISO 포맷으로 표현하고, 없으면 null입니다."),
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

prompt_template = PromptTemplate(
    template="""다음 사용자 입력에서 의도를 파악하고, 일정 관련 정보를 추출하세요.
    참고로 오늘은 {today}이고 {today_weekday}이다. 일정 종료 시간에 대한 언급이 없는 경우에는 시작시간으로부터 1시간이후에 일정이 종료되는 것으로 해줘.
    오늘 날짜를 이용해서 오늘, 내일, 모레, 다음주 등에 대한 정보를 정확한 날짜로 변경해줘.
    일정 조회를 하는 경우에 다음주나 다다음주 등의 경우에는 해당 주의 월요일 0시를 일정 시작 시간으로, 일요일 23시 59분을 일정 종료 시간으로 해줘.
    다음 달의 경우에는 해당 달의 1일 0시가 시작 시간, 마지막 날 23시 59분이 종료 시간으로 해주면 될 것 같애.
    {format_instructions}
    사용자 입력: {user_input}
    """,
    input_variables=["user_input", "today", "today_weekday"],
    partial_variables={"format_instructions": format_instructions}
)
intent_chain = prompt_template | llm | output_parser

def info_extractor(question):
    today, today_weekday = present_time()
    response = intent_chain.invoke({"user_input": question, "today": today, "today_weekday": today_weekday})

    return response['intent'], response['start_time'], response['end_time'], response['summary']