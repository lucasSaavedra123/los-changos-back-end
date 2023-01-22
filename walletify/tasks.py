from django.core.mail import send_mail



def notify_expiration_expenses():
    from budgets.models import FutureExpenseDetail
    print("Sending Emails!!!")
    string_email = "¡ACUERDATE DE PAGAR!" + '\n\n' + "Recuerda que se vence el siguientes pagos: "

    for future_expense_detail in FutureExpenseDetail.objects.all():

        if future_expense_detail.should_be_notified():
            string_email += '\n\n' + "-Nombre de gasto futuro:" + future_expense_detail.name + '\n\n' + 'Valor: ' + str(future_expense_detail.value) + '\n\n' + 'Fecha de vencimiento: ' + str(future_expense_detail.expiration_date) + '\n\n' + 'Categoría: ' + future_expense_detail.category.name


    send_mail(
        '[IMPORTANTE] ¡ACUERDATE DE PAGAR!',
        string_email + '\n\n\n\n' + '¡Gracias por usar Walletify!',
        'notifications@walletify.com',
        [future_expense_detail.assigned_budget.user.email],
        fail_silently=False,
    )
