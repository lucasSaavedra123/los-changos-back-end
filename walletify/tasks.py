from django.core.mail import send_mail



def notify_expiration_expenses():
    from budgets.models import FutureExpenseDetail
    from budgets.models import Budget
    from users.models import User
    print("Info: Users are notified...")

    for user in User.objects.all():

        current_budget = Budget.current_budget_of(user)

        if current_budget is not None:
            future_expenses = FutureExpenseDetail.objects.filter(assigned_budget=current_budget)
            future_expenses = [detail for detail in future_expenses if detail.should_be_notified()]

            if len(future_expenses) > 0:

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
