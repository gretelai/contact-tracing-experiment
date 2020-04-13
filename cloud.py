from collections import defaultdict

from handset import DTK


class Cloud:

    def __init__(self):
        self.diagnosis_keys = defaultdict(list)

    def add_dtk(self, uuid, dtk: DTK):
        self.diagnosis_keys[uuid].append(dtk)

    def download_dtks(self):
        """In theory, we shouldn't be sending
        handset UUIDs back
        """
        out = []
        for _, keys in self.diagnosis_keys.items():
            out.extend(keys)
        return out
