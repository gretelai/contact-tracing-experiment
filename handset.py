import secrets
import uuid
import datetime
from numbers import Number
import hmac
from hashlib import sha256
from dataclasses import dataclass, InitVar
from typing import Type
import calendar

from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

from cloud import Cloud

ONE_DAY = 86400


def get_tin(seconds_in_day):
    return int(seconds_in_day / 600)


@dataclass
class DTK:
    seed_epoch: InitVar[Number]
    day_number: int = None
    dt: Type[datetime.datetime] = None
    base_epoch: Number = None
    day_str: str = None
    key: str = None

    def __post_init__(self, seed_epoch: Number):
        self.day_number = int(seed_epoch / ONE_DAY)
        self.dt = datetime.datetime.utcfromtimestamp(seed_epoch).replace(hour=0, minute=0, second=0, microsecond=0)  # noqa
        self.base_epoch = calendar.timegm(self.dt.timetuple())
        self.day_str = self.dt.isoformat()


@dataclass
class Contact:
    rpi: str
    epoch: Type[Number]
    ts: str
    relation: str
    uuid: str


class Handset:

    def __init__(self, relation):
        # assign a UUID to the handset, this would really be a IMEI, etc but
        # doesn't really matter for our purposes
        self.uuid = uuid.uuid4().hex

        # NOTE: this is to help provide context during the
        # simulation
        self.relation = relation

        # generate the single Tracing Key for the handset
        self.tracing_key = secrets.token_hex(32).encode()

        # this map should store the daily trace keys for
        # this handset. indexed by the day number
        self.daily_trace_keys = {}

        # this will hold all RPIs that are transmitted from proximity
        self.other_rpis = set()

    def create_daily_tracing_key(self, seed_epoch: Number):  # noqa
        dtk = DTK(seed_epoch)
        key = HKDF(
            self.tracing_key,
            16,  # 16 byte key
            b'',
            SHA256,
            num_keys=1,
            context=('CT-DTK' + str(dtk.day_number)).encode()
        ).hex()
        dtk.key = key
        self.daily_trace_keys[dtk.day_number] = dtk
        return key

    @staticmethod
    def _rpi(k: bytes, tin: int):
        return hmac.new(k, ('CT-RPI'+str(tin)).encode(), sha256).hexdigest()  # noqa

    def get_rpi(self, seed_epoch: Number):
        # first we need to get the daily trace key
        # for this epoch
        day_number = DTK(seed_epoch).day_number
        dtk = self.daily_trace_keys[day_number].key

        # next we need to get the TIN for this epoch
        # NOTE: not truncating this to the 16 bytes as it doesn't really matter
        # for this implementation
        tin = get_tin(seed_epoch - (seed_epoch - (seed_epoch % 86400)))

        return self._rpi(dtk.encode(), tin)

    @staticmethod
    def generate_rpis_from_dtk(dtk: DTK):
        """Given a DTK, generate all of the
        possible RPIs for that day. Which means we just calculate
        all the RPIs for all 144 possible TINs for that key
        """
        out = {}
        key = dtk.key.encode()
        for i in range(0, 144):
            offset = i*600
            tmp_rpi = Handset._rpi(key, i)
            out[tmp_rpi] = dtk.base_epoch + offset # noqa
        return out

    def receive_rpi(self, rpi):
        self.other_rpis.add(rpi)

    def determine_contacts(self, cloud: Cloud):
        remote_keys = cloud.download_dtks()

        # build a master map of all RPIs to timeframes
        master_map = {}

        dtk: DTK
        for dtk in remote_keys:
            tmp_map = self.generate_rpis_from_dtk(dtk)
            master_map.update(tmp_map)

        remote_rpis = set(list(master_map.keys()))
        inter = remote_rpis & self.other_rpis

        res = [Contact(
            rpi=rpi,
            epoch=master_map[rpi],
            ts=datetime.datetime.utcfromtimestamp(master_map[rpi]).isoformat(),
            relation=self.relation,
            uuid=self.uuid
            ) for rpi in inter]  # noqa

        return sorted(res, key=lambda t: t.epoch)
