from collections import defaultdict


class Cloud:

    def __init__(self):
        self.diagnosis_keys = defaultdict(list)

    def add_dtk(self, uuid, dtk):
        """We track all DTKs for a given handset UUID, but really
        you don't need to do this
        """
        self.diagnosis_keys[uuid].append(dtk)

    def download_dtks(self):
        """In theory, we shouldn't be sending
        handset UUIDs back or really need
        to collect them in the first place
        """
        out = []
        for _, keys in self.diagnosis_keys.items():
            out.extend(keys)
        return out
