from users.models import User
from categories.models import Category
from budgets.models import Budget


a_user = User.objects.create(firebase_uid='randomrandomrandomrandomrand', email='random@random.com')
a_budget = Budget.objects.create(user=a_user, initial_date='2023-01-01', final_date='2023-12-31')
all_categories = Category.objects.all()

a_budget.add_future_expense(category=all_categories[0], value=100, name='random expense', expiration_date='2023-02-9')
a_budget.add_future_expense(category=all_categories[2], value=250, name='random expense', expiration_date='2023-02-9')
a_budget.add_future_expense(category=all_categories[1], value=320, name='random expense', expiration_date='2023-02-7')
a_budget.add_future_expense(category=all_categories[0], value=100, name='random expense', expiration_date='2023-02-10')
a_budget.add_future_expense(category=all_categories[0], value=780, name='random expense', expiration_date='2023-02-9')
