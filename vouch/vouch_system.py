from . import db

import math
import sqlite3



DFLT_CONFIG = {
    "bootstrap": True, # to allow first member to join without vouches
    "vouch_min": -1,
    "vouch_max": 1
}


def _init_db():
    with db.connect() as conn:
        db.create_config_table(conn)
        db.create_members_table(conn)
        db.create_vouches_table(conn)

        # ensure config table is initialized properly
        for key, value in DFLT_CONFIG.items():
            # Add missing options with dflt value
            if db.get_config_value(conn, key) is None:
                db.create_config(conn, (key, value))


def _approveMembership(vouchee_id):
    with db.connect() as conn:
        db.create_member(conn, (vouchee_id,))


def _isApproved(vouchee_id):
    with db.connect() as conn:
        total_members = db.get_member_count(conn)
        value = db.get_vouchee_value(conn, vouchee_id)
        approve = thresholdApprove()

    if value is None:
        return None

    if approve <= value:
        return True
    return False


def _isBootstrappable():
    with db.connect() as conn:
        result = int(db.get_config_value(conn, 'bootstrap'))
    return result


# check to see if non-member should be a member
#   membership is/isn't updated accordingly
def _membershipCheck(vouchee_id):
    if isMember(vouchee_id): # already a member
        return
    if not _isApproved(vouchee_id): # not even vouch
        return
    _approveMembership(vouchee_id)


def _vouchValueInRange(value):
    with db.connect() as conn:
        vouch_min = int(db.get_config_value(conn, 'vouch_min'))
        vouch_max = int(db.get_config_value(conn, 'vouch_max'))

    if value < vouch_min or vouch_max < value:
        return False
    return True


# returns the current vouch count required for membership
def approvalThreshold():
    with db.connect() as conn:
        total_members = db.get_member_count(conn)
    if total_members < 2:
        return 0
    else:
        return math.floor(math.log(total_members, 1.4))


# One-time bootstrapping of first member
def bootstrap(member_id):
    if not _isBootstrappable():
        raise Exception('Bootstrap denied. Cannot bootstrap more than once!')

    with db.connect() as conn:
        db.update_config_value(conn, 'bootstrap', False)

    _approveMembership(member_id)


def getVoucheeValue(vouchee_id):
    with db.connect() as conn:
        return db.get_vouchee_value(conn, vouchee_id)


def isMember(vouchee_id):
    with db.connect() as conn:
        membership = db.get_member(conn, vouchee_id)

    if membership:
        return True
    else:
        return False


def vouch(voucher_id, vouchee_id, value):
    if not _vouchValueInRange(value):
        raise Exception('Vouch value is outside expected range!')
    if voucher_id == vouchee_id:
        raise Exception('You can\'t vouch for yourself!')
    if not isMember(voucher_id):
        raise Exception('Only members can vouch for other users!')

    with db.connect() as conn:
        value = db.get_vouch_value(conn, voucher_id, vouchee_id)
        if value is None:
            db.create_vouch(conn, (voucher_id, vouchee_id, value))
        else:
            db.update_vouch_value(conn, voucher_id, vouchee_id, value)

    # perform membership check on vouchee
    _membershipCheck(vouchee_id)



_init_db()
