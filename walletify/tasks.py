from django.core.mail import send_mail
from budgets.models import FutureExpenseDetail


"""
send_mail(
    'Subject here',
    'Here is the message.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)

@periodic_task(
run_every=(crontab(hour=3, minute=34)), #runs exactly at 3:34am every day
name="Dispatch_scheduled_mail",
reject_on_worker_lost=True,
ignore_result=True)
def schedule_mail():
    message = render_to_string('app/schedule_mail.html')
    mail_subject = 'Scheduled Email'
    to_email = getmail
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()
"""


def notify_expiration_expenses():
    print("Sending Email!!!")