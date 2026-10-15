import numpy as np
import pandas as pd
import pytest
from src.sample_data_generator import generate_synthetic_market_data
from src.data_loader import validate_market_data,add_datetime_and_sort
from src.feature_engineering import merge_trade_snapshot, add_bid_ask_imbalance, reshape_bid1p_wide
from src.resampling import downsample_market_data
from src.order_book_analysis import classify_last_price,detect_free_hole_additions,category_proportions

@pytest.fixture(scope="module")
def sample():return generate_synthetic_market_data(n_stocks=3,dates=[20210104],n_snapshots=1200,seed=42)

def test_original_counts(sample):
    s,t=sample
    assert len(s)==3600 and len(t)==720
    assert validate_market_data(s,"snapshot")["passed"]
    assert validate_market_data(t,"trade")["passed"]

def test_no_duplicates(sample):
    s,t=sample
    assert validate_market_data(s)["duplicated_keys"]==0
    assert validate_market_data(t)["duplicated_keys"]==0

def test_wide_shape(sample):assert reshape_bid1p_wide(sample[0]).shape==(1200,5)

def test_imbalance_range(sample):
    d=add_bid_ask_imbalance(sample[0])
    assert d.obi5.between(-1,1).all()
    assert d.bid_ask_imba.between(-1,1).all()
    assert (d.spread>0).all()

def test_alignment_preserves_rows(sample):
    d=merge_trade_snapshot(*sample)
    assert len(d)==3600
    assert (d.trade_age_seconds.dropna()>=0).all()
    assert d.trade_observed.sum()==720

def test_shuffled_alignment_never_leaks_future(sample):
    s,t=sample
    sample_s=s.iloc[:4].sample(frac=1,random_state=23)
    sample_t=t.loc[(t.id==1)&(t.date==20210104)].iloc[1:3]
    out=merge_trade_snapshot(sample_s,sample_t,max_staleness_seconds=None)
    past=out.loc[out.datetime<sample_t.datetime.min()]
    assert past["last"].isna().all()
    assert (out.trade_datetime.dropna()<=out.datetime[out.trade_datetime.notna()]).all()

def test_stale_trade_is_not_forward_filled_forever(sample):
    s,t=sample
    d=merge_trade_snapshot(s.loc[(s.id==1)].head(20),t.loc[t.id==1].head(1),max_staleness_seconds=6)
    assert d["last"].notna().sum()==3
    assert d["last"].isna().any()

def test_duplicate_trade_rejected(sample):
    s,t=sample
    with pytest.raises(ValueError,match="Duplicate trade"):
        merge_trade_snapshot(s,t.iloc[[0,0]])

def test_invalid_date_rejected():
    with pytest.raises(ValueError,match="Invalid date/time"):
        add_datetime_and_sort(pd.DataFrame({"id":[1],"date":[20211399],"time":["bad"]}))

def test_crossed_quote_rejected(sample):
    d=sample[0].head(1).copy()
    d.loc[d.index[0],"ask1p"]=d.loc[d.index[0],"bid1p"]
    q=validate_market_data(d,"snapshot")
    assert not q["passed"] and any(i["code"]=="crossed_or_invalid_levels" for i in q["issues"])

def test_rolling_downsample(sample):
    d=add_bid_ask_imbalance(sample[0])
    joined=merge_trade_snapshot(d,sample[1])
    down=downsample_market_data(joined)
    assert len(down)==18
    assert down.bid1p_realized_quote_vol.dropna().ge(0).all()

def test_downsample_invalid_interval(sample):
    d=merge_trade_snapshot(*sample)
    with pytest.raises(ValueError): downsample_market_data(d,0)

def test_trade_classification_excludes_stale(sample):
    d=merge_trade_snapshot(*sample)
    out=classify_last_price(d)
    assert out.last_category.notna().sum()<=720
    assert out.loc[~out.trade_observed,"last_category"].isna().all()
    counts=category_proportions(out)
    assert np.allclose(counts.sum(axis=1),1)

def test_free_hole_candidates(sample):
    d=detect_free_hole_additions(sample[0])
    assert len(d)>0
    assert set(d.side)=={"bid","ask"}
    assert d.quantity.gt(0).all()

def test_no_cross_session_hole(sample):
    d=sample[0]
    only=d.loc[d.id==1].head(1)
    assert detect_free_hole_additions(only).empty
