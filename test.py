import time

import handset
import life


def test_rpik():
    now = time.time()

    tek = handset.TEK(seed_epoch=now)
    rpik = handset.RPIK(tek)

    now += 6*3600
    e = handset.get_enin(now)
    check = rpik.get_proximity_id(e)

    all_rpis = rpik.enumerate_proximity_ids()
    assert check in all_rpis.keys()


def test_contact():
    subj = handset.Handset('subj')
    other = handset.Handset('other')

    now = time.time()

    subj.create_tek(now)
    other.create_tek(now)

    # 6 hours later we interact
    now += 6*3600
    subj_rpi = subj.get_rpi(now)
    other_rpi = other.get_rpi(now)
    subj.receive_rpi(other_rpi)
    other.receive_rpi(subj_rpi)

    # upload subject TEK to the cloud
    cloud = life.Cloud()
    subj.upload_teks(cloud)

    check = other.determine_contacts(cloud)
    assert len(check) == 1
