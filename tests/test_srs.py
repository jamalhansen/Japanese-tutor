from japanese_tutor.srs import SM2

def test_sm2_first_review_correct():
    # rating 5, rep 0, interval 0, ef 2.5
    interval, rep, ef = SM2.calculate_next_review(5, 0, 0, 2.5)
    assert interval == 1
    assert rep == 1
    assert ef > 2.5

def test_sm2_second_review_correct():
    # rating 5, rep 1, interval 1, ef 2.6
    interval, rep, ef = SM2.calculate_next_review(5, 1, 1, 2.6)
    assert interval == 6
    assert rep == 2

def test_sm2_third_review_correct():
    # rating 5, rep 2, interval 6, ef 2.7
    interval, rep, ef = SM2.calculate_next_review(5, 2, 6, 2.7)
    assert interval == 16 # round(6 * 2.7) = 16.2
    assert rep == 3

def test_sm2_fail_resets():
    interval, rep, ef = SM2.calculate_next_review(0, 5, 100, 2.5)
    assert interval == 1
    assert rep == 0
    assert ef < 2.5
