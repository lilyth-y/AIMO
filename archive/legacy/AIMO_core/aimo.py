import pandas as pd

class MockEnv:
    def __init__(self):
        self.problems = [
            {'id': '001', 'problem': 'What is 1 + 1?'},
            {'id': '002', 'problem': 'Find the value of x if 2x = 10.'},
            {'id': '003', 'problem': 'Calculate the area of a square with side 5.'}
        ]
        self.iter_count = 0

    def iter_test(self):
        for p in self.problems:
            df_test = pd.DataFrame([p])
            df_sample = pd.DataFrame([{'id': p['id'], 'answer': 0}])
            yield df_test, df_sample

    def predict(self, sample_submission):
        print(f"[MockEnv] Received prediction: {sample_submission.to_dict(orient='records')}")

def make_env():
    return MockEnv()
