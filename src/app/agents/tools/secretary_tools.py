from langchain.tools import tool


@tool
def schedule_task(prompt: str, schedule: str) -> bool:
    print('Not implemented')

    return True


@tool
def notify_email(email: str, msg: str) -> bool:
    print(f'Send email to {email} with: {msg}')
