from utils.data_generator import DataGenerator

gen          = DataGenerator()
customers    = gen.generate_customers(100)
transactions = gen.generate_transactions(500)

print(f"Customers:    {len(customers)}")
print(f"Transactions: {len(transactions)}")
print(gen.get_issue_summary())