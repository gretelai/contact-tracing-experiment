import random

from handset import Handset
from cloud import Cloud

ONE_HOUR = 3600
ONE_DAY = 86400


def get_handsets(count):
    return [Handset() for _ in range(0, count)]


class Life:

    def __init__(self, start_time: int):
        self.family = get_handsets(random.randrange(2, 8))
        self.friends = get_handsets(random.randrange(10, 20))
        self.coworkers = get_handsets(random.randrange(15, 40))
        self.others = get_handsets(random.randrange(40, 100))

        self.all_handsets = self.family + self.friends + self.coworkers + self.others  # noqa

        # this is the current date/time for the simulation
        self.time = start_time

        # the person that eventually will contract C19
        self.subject = Handset()

        self.cloud = Cloud()

    def start(self):
        for _ in range(0, 5):
            self.weekday()

        self.weekend()
        self.weekend()

        for _ in range(0, 5):
            self.weekday()

        self.weekend()
        self.weekend()

        # assume a positive diagnosis
        # so that would mean the subject's
        # past DTKs are uploaded to the cloud
        # to be made available to all other
        # users
        for _, dtk in list(self.subject.daily_trace_keys.items()):
            self.cloud.add_dtk(self.subject.uuid, dtk)

    def find_contacts(self):
        """Go through all of the handsets and find
        which ones were in contact
        """
        contacts = []
        for handset in self.all_handsets:
            contacts.append(handset.determine_contacts(self.cloud))
        return sorted(contacts, key=lambda c: len(c), reverse=True)

    def mingle(self, other: Handset):
        subject_rpi = self.subject.get_rpi(self.time)
        other_rpi = other.get_rpi(self.time)

        other.receive_rpi(subject_rpi)
        self.subject.receive_rpi(other_rpi)

    def hour(self, focus: str):
        self.time += ONE_HOUR

        if focus == 'family':
            other = random.choice(self.family)
            self.mingle(other)

        if focus == 'coworker':
            other = random.choice(self.coworkers)
            self.mingle(other)
            other = random.choice(self.coworkers)
            self.mingle(other)

        if focus == 'friends':
            other = random.choice(self.friends)
            self.mingle(other)

        if focus == 'others':
            other = random.choice(self.others)
            self.mingle(other)

    def weekday(self):
        day_start = self.time  # save the first hour of our day

        # starting a new day, generate the DTK
        # for each handset
        self.subject.create_daily_tracing_key(self.time)
        for h in self.all_handsets:
            h.create_daily_tracing_key(self.time)

        # spend a couple hours in the morning with family
        self.hour('family')
        self.hour('family')

        # stop for some breakfast / coffee on the way to work?
        if random.choice([1, 2, 3]) == 1:
            self.hour('others')

        # work, work!
        self.hour('coworker')
        self.hour('coworker')
        self.hour('coworker')

        # lunch / gym?
        if random.choice([1, 2, 3]) == 1:
            self.hour('others')

        # moar work
        self.hour('coworker')
        self.hour('coworker')

        # happy hour?
        if random.choice([1, 2, 3, 4, 5]) == 1:
            self.hour('friends')

        # back home
        self.hour('family')
        self.hour('family')

        # fast forward to the next morning
        self.time = day_start + ONE_DAY

    def weekend(self):
        day_start = self.time

        self.subject.create_daily_tracing_key(self.time)
        for h in self.all_handsets:
            h.create_daily_tracing_key(self.time)

        self.hour('family')
        self.hour('family')
        self.hour('family')

        # errands or whatever
        self.hour('others')

        # quick meetup
        self.hour('friends')

        # back home
        self.hour('family')
        self.hour('family')

        # party!
        self.hour('friends')
        self.hour('friends')
        self.hour('friends')

        # afterparty
        self.hour('others')
        self.hour('others')

        self.time = day_start + ONE_DAY
