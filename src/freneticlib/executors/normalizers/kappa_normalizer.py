from freneticlib.executors.normalizers.abstract_normalizer import AbstractNormalizer


class KappaNormalizer(AbstractNormalizer):
    def __init__(self, global_bound: float = 0.07, local_bound: float = 0.05):
        self.global_bound = global_bound
        self.local_bound = local_bound

    def normalize(self, test):
        test[0] = max(min(test[0], self.global_bound), -self.global_bound)
        for i in range(1, len(test)):
            previous = test[i - 1]
            min_bound = max(-self.global_bound, previous - self.local_bound)
            max_bound = min(self.global_bound, previous + self.local_bound)
            test[i] = max(min(test[i], max_bound), min_bound)
        return test
