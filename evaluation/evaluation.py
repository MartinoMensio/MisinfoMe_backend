import os
import tqdm
import random
import requests
import pandas as pd
from multiprocessing.pool import ThreadPool
import sklearn.metrics as metrics
import matplotlib
matplotlib.use('agg')
import seaborn as sns

# from https://colab.research.google.com/drive/1p7-N3CZrVBbV6DqU6wcydAM7yRoqhXXC?usp=sharing#scrollTo=3e0vudM4h4Lw

remote = False
subset = 'all' # one of train test rest all
# retrieve_predictions = False

if remote:
    # labels from dashboard
    dboard_url = 'https://dashboard.coinform.eu/api/dboard'
    coll_name = 'misinfome_tweet_reviews'
    fields = 'id,misinfome_label,content,content_language,lang,lang_orig'

    # query test
    resp = requests.get('%s/%s/select?q=*:*&wt=json&rows=1&fl=%s' % (dboard_url, coll_name, fields))
    # print(resp.text)
    # print(resp.ok, resp.json())

    # full dataset
    resp = requests.get('%s/%s/select?q=*:*&wt=json&rows=4600&fl=%s' % (dboard_url, coll_name, fields))
    dataset = resp.json()['response']['docs']
    # print(len(dataset),type(dataset))

    # to pandas
    df = pd.DataFrame.from_records(data=dataset)
    # print(df.sample(n=4))
    # print(len(dataset), type(dataset))

else:
    if subset == 'all':
        dfs = []
        for other in ['train', 'test', 'rest']:
            df2 = pd.read_csv(f'silver_labels/coinform4550_{other}.csv')
            dfs.append(df2)
        df = pd.concat(dfs, ignore_index=True)
        retrieve_predictions = False
    else:
        df = pd.read_csv(f'silver_labels/coinform4550_{subset}.csv')
        retrieve_predictions = not os.path.exists(f'predictions_{subset}.csv')
    # print(df.sample(n=4))

# show stats
print(df.head())
print(df.groupby('misinfome_label').count())# ['id'].plot.pie(figsize=(5,5))

# fetch predictions
# test
# acred_fields = 'id,credibility_label,credibility_score,credibility_confidence'
# resp = requests.get('%s/%s/select?q=*:*&wt=json&rows=6&fl=%s' % (dboard_url, coll_name, acred_fields))
# print(resp.ok, resp.json())

# # full set of predictions
# resp = requests.get('%s/%s/select?q=*:*&wt=json&rows=4600&fl=%s' % (dboard_url, coll_name, acred_fields))
# acred_preds = resp.json()['response']['docs']
# acred_preds_df = pd.DataFrame(acred_preds)
# acred_preds_df.sample(n=4)

# def acred_credlabel_to_predlabel(row):
#   # updated policy intervals: https://github.com/co-inform/policy_manager/blob/master/src/main/resources/rules/deployment/credibility_mapping/misinfome.json
#   c2p = {
#       'credible': 'credible',
#       'mostly credible': 'mostly_credible',
#       'credibility uncertain': 'uncertain',
#       'mostly not credible': 'not_credible',
#       'not credible': 'not_credible',
#       'not verfiable': 'not_verifiable'
#   }
#   clabel = row.get('credibility_label', None)
#   tweet_id = row['id']
#   plabel = c2p.get(clabel, 'not_verifiable') # by default predict not_verifiable
#   return plabel

def prediction_to_coinform_label(row):
    # https://github.com/co-inform/policy_manager/blob/master/src/main/resources/rules/deployment/credibility_mapping/misinfome.json
    cred = row['credibility_value']
    conf = row['credibility_confidence']
    if conf < 0.5:
        return 'not_verifiable'
    if cred <= -0.5:
        return 'not_credible'
    if cred <= 0.25:
        return 'uncertain'
    if cred <= 0.6:
        return 'mostly_credible'
    return 'credible'

def get_one(t_id):
    res = requests.get(f'http://localhost:5000/misinfo/api/credibility/tweets/{t_id}')
    # res = requests.get(f'https://misinfo.me/misinfo/api/credibility/tweets/{t_id}')
    return t_id, res
if retrieve_predictions:
    predictions = []
    with ThreadPool(8) as pool: # TODO multithread
        for tweet_id, res in tqdm.tqdm(pool.imap_unordered(get_one, list(df['id'])),
            desc='fetching predictions', total=len(df)):
            try:
                res.raise_for_status()
                response = res.json()
                predictions.append({
                    'id': tweet_id,
                    'credibility_value': response['credibility']['value'],
                    'credibility_confidence': response['credibility']['confidence'],
                    'not_found': 'exception' in response, # tweet deleted, but evaluation available
                    'evaluation_available': True
                })
            except Exception as e:
                print(tweet_id, e)
                predictions.append({
                    'id': tweet_id,
                    'credibility_value': 0,
                    'credibility_confidence': 0,
                    'not_found': True,
                    'evaluation_available': False
                })

    # print(predictions)
    pred_df = pd.DataFrame(predictions)

    # pred_df['pred_label'] = pred_df.apply(prediction_to_coinform_label, axis=1)
    # print(pred_df)

    pred_df.to_csv(f'predictions_{subset}.csv')
else:
    if subset == 'all':
        pred_dfs = []
        for other in ['train', 'test', 'rest']:
            df2 = pd.read_csv(f'predictions_{other}.csv')
            pred_dfs.append(df2)
        pred_df = pd.concat(pred_dfs, ignore_index=True)
    else:
        pred_df = pd.read_csv(f'predictions_{subset}.csv')


print(list(pred_df.columns))
pred_df['pred_label'] = pred_df.apply(prediction_to_coinform_label, axis=1)




# merge
merged_df = pd.merge(df, pred_df, on='id')
# print(merged_df.shape)
# print(merged_df.sample(n=3))

print(metrics.accuracy_score(merged_df['misinfome_label'], merged_df['pred_label']))


merged_df['acred_predlabel'] = merged_df['pred_label']

mcie_error_mapping = {
      'not_credible': {
          'credible': 1.0,
          'mostly_credible': 0.75,
          'uncertain': 0.5, 
          'not_credible': 0.0, 
          'not_verifiable': 0.5 
      }, 
      'uncertain': {
          'credible': 0.5,
          'mostly_credible': 0.25,
          'uncertain': 0.0, 
          'not_credible': 0.5, 
          'not_verifiable': 0.1 
      }, 
      'not_verifiable': {
          'credible': 0.5,
          'mostly_credible': 0.5,
          'uncertain': 0.1, 
          'not_credible': 0.5, 
          'not_verifiable': 0.0
      }, 
      'credible': {
          'credible': 0.0,
          'mostly_credible': 0.25,
          'uncertain': 0.5, 
          'not_credible': 1.0, 
          'not_verifiable': 0.5
      },
      'mostly_credible': {
          'credible': 0.25,
          'mostly_credible': 0.0,
          'uncertain': 0.5, 
          'not_credible': 1.0, 
          'not_verifiable': 0.5
      },
      'check_me': {
          'credible': 0.0,
          'mostly_credible': 0.0,
          'uncertain': 0.0, 
          'not_credible': 0.0, 
          'not_verifiable': 0.0
      } 
  }

def mcie_score(y_true, y_pred):
    '''Computes the Mean Co-inform Error'''
    assert len(y_true) == len(y_pred), 'Lengths do not match %s != %s' % (
        len(y_true), len(y_pred))
    errors = [mcie_error_mapping[yt][yp] for yt, yp in zip(y_true, y_pred)]
    return sum(errors)/len(errors)

def max_mcie_error(y_true):
    max_errors = [max(mcie_error_mapping[yt].values()) for yt in y_true]
    return sum(max_errors)/len(y_true)

def norm_mcie_score(y_true, y_pred):
    '''Computes the normalised Mean Co-inform Error
    The error is normalised to the range of minimum error (always 0) and 
    maximum error (which depends on the labels in y_true)
    '''
    assert len(y_true) == len(y_pred), 'Lengths do not match %s != %s' % (
        len(y_true), len(y_pred))
    mcie = mcie_score(y_true, y_pred)
    return mcie/max_mcie_error(y_true)

def mci_acc_score(y_true, y_pred):
    return 1.0 - norm_mcie_score(y_true, y_pred)


def build_preds_to_compare(ci_df):
  silver_labels = ci_df['misinfome_label'].to_list()
  acred_labels = ci_df['acred_predlabel'].to_list()
  N = len(silver_labels)
  baseline_not_credible = ['not_credible' for i in range(N)]
  baseline_not_verifiable = ['not_verifiable' for i in range(N)]
  baseline_credible = ['credible' for i in range(N)]
  baseline_mostly_cred = ['mostly_credible' for i in range(N)]
  baseline_uncertain = ['uncertain' for i in range(N)]
  baseline_random = [random.choice(['not_credible', 'uncertain', 'not_verifiable', 
                                    'credible', 'mostly_credible'])
                      for i in range(N)]

  return {
      'y_true': silver_labels,
      'y_preds': {
        'acred': acred_labels,
        'baseline_not_cred': baseline_not_credible,
        'baseline_not_verif': baseline_not_verifiable,
        'baseline_uncertain': baseline_uncertain,
        'baseline_mostly_cred': baseline_mostly_cred,
        'baseline_cred': baseline_credible,
        'baseline_random': baseline_random
      }
  }


def compare_preds(preds_to_compare, metric_fns):
    rows = []
    y_true = preds_to_compare['y_true']
    assert type(y_true) is list
    for pred_label, y_pred in preds_to_compare['y_preds'].items():
        assert type(y_pred) is list
        row = {'system': pred_label,
            **{m_label: m_fn(y_true, y_pred)
                for m_label, m_fn in metric_fns.items()}}
        rows.append(row)
    return pd.DataFrame(rows)\

metric_fns = {
    'accuracy': metrics.accuracy_score, 
    'MCiE': mcie_score,
    'norm_MCiE': norm_mcie_score,
    'MCi_acc': mci_acc_score}

preds_to_compare = build_preds_to_compare(merged_df)
print(compare_preds(preds_to_compare, metric_fns))



def plot_confmat(y_true, y_pred, outfile=None, 
                 title=None, xylabels=True):
  labels = [ 'credible', 'mostly_credible', 'uncertain', 'not_verifiable', 'not_credible', 'check_me']
  short_labels = ['credible', '≈cred', 'uncertain', '¬verifiable', '¬credible', '??']
  cf_matrix = metrics.confusion_matrix(y_true, y_pred, labels=labels)
  #print('confmat', type(cf_matrix), '\n', cf_matrix)
  if not title:
    mci_acc = mci_acc_score(y_true, y_pred)
    title = 'Confusion credibility: acc=%.3f, ci_acc=%.3f, n=%d)' % (
          metrics.accuracy_score(y_true, y_pred), mci_acc, len(y_true))
  return sns_confmat(cf_matrix, short_labels, title, outfile=outfile, xylabels=xylabels)

def sns_confmat(cf_matrix, labels, title, outfile=None, xylabels=True):
  sns.set(font_scale=1.7)
  ax = sns.heatmap(cf_matrix, annot=True, xticklabels=labels, yticklabels=labels, fmt='g', cmap='Blues')
  if xylabels:
    ax.set_xlabel('Predicted'); ax.set_ylabel('True labels');
  ax.set_title(title)
  ax.xaxis.set_ticklabels(labels); ax.yaxis.set_ticklabels(labels)
  ax.xaxis.set_tick_params(labelrotation=45.0), ax.yaxis.set_tick_params(labelrotation=0.0)
  if outfile:
    fig = ax.get_figure()
    fig.savefig(outfile, dpi=300, bbox_inches='tight')
  return ax


plot = plot_confmat(preds_to_compare['y_true'], preds_to_compare['y_preds']['acred'], outfile=f'confusion_{subset}.png')


# train 404: 53 over 353
# test 404: more than 50 ??? over 400