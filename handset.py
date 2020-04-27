import uuid
import datetime
from numbers import Number
from dataclasses import dataclass, InitVar

from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


ONE_DAY = 86400


def get_enin(seed_time: float):
    return int(seed_time / 600)


@dataclass
class TEK:
    seed_epoch: InitVar[Number] = None
    enin: int = None
    key: bytes = None

    def __post_init__(self, seed_epoch: Number):
        if not self.enin:
            self.enin = get_enin(seed_epoch)
        if not self.key:
            self.key = get_random_bytes(16)


class RPIK:

    def __init__(self, tek: TEK):
        self.key = HKDF(
                    tek.key,
                    16,  # 16 byte key
                    b'',
                    SHA256,
                    num_keys=1,
                    context=('EN-RPIK').encode()
            )
        self.tek = tek
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def get_proximity_id(self, enin):
        data = ('EN-RPI' + str(enin)).encode()
        enc = self.cipher.encrypt(pad(data, AES.block_size))
        self.cipher = AES.new(self.key, AES.MODE_ECB)
        return enc.hex()

    def enumerate_proximity_ids(self):
        # map each RPI by the ENIN, this way we can
        # easily find which slice of time an RPI
        # was most likely observed in
        pid_map = {}
        enin = self.tek.enin
        for _ in range(0, 144):
            pid_map[self.get_proximity_id(enin)] = enin
            enin += 6
        return pid_map


@dataclass
class Contact:
    rpi: str = None
    enin: int = None
    ts: str = None
    relation: str = None
    uuid: str = None

    def __post_init__(self):
        self.ts = datetime.datetime.utcfromtimestamp(self.enin*600).isoformat()  # noqa


class Handset:

    def __init__(self, relation):
        # assign a UUID to the handset, this would really be a IMEI, etc but
        # doesn't really matter for our purposes
        self.uuid = uuid.uuid4().hex

        # NOTE: this is to help provide context during the
        # simulation
        self.relation = relation

        # this map should store the daily trace keys for
        # this handset. indexed by the enin that was generated
        # on creation of the TEK
        self.daily_teks = {}

        # this will hold all RPIs that are transmitted from proximity
        self.other_rpis = set()

        self.curr_tek = None
        self.curr_rpik = None

    def create_tek(self, seed_epoch: Number):
        tek = TEK(seed_epoch=seed_epoch)
        self.daily_teks[tek.enin] = tek
        self.curr_tek = tek
        self.curr_rpik = RPIK(tek)

    def upload_teks(self, cloud):
        for _, tek in self.daily_teks.items():
            cloud.add_tek(tek)

    def get_rpi(self, seed_epoch: Number):
        return self.curr_rpik.get_proximity_id(get_enin(seed_epoch))

    def receive_rpi(self, rpi):
        self.other_rpis.add(rpi)

    def determine_contacts(self, cloud):
        remote_keys = cloud.diagnosis_keys

        # build a master map of all RPIs to timeframes
        master_map = {}

        tek: TEK
        for tek in remote_keys:
            tmp_rpik = RPIK(tek)
            tmp_map = tmp_rpik.enumerate_proximity_ids()
            master_map.update(tmp_map)

        remote_rpis = set(list(master_map.keys()))
        inter = remote_rpis & self.other_rpis

        res = [Contact(
            rpi=rpi,
            enin=master_map[rpi],
            relation=self.relation,
            uuid=self.uuid
            ) for rpi in inter]  # noqa

        return sorted(res, key=lambda t: t.enin)
