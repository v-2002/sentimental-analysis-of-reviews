import nlp as nlp
from textblob import TextBlob
from nltk import *
from nltk import tokenize
import pandas as pd
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS
import spacy
import re


# python -m pip install nltk
# python -m nltk.downloader stopwords
# python -m pip install textblob
# python -m spacy download en_core_web_sm


# text = "very bad"
# print(TextBlob(text).sentiment.polarity)


def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags 
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)


def space(comment):
    doc = nlp(comment)
    return " ".join([token.lemma_ for token in doc])


def analysis():
    df = pd.read_csv("reviews.csv")
    # print(df.body[1])
    pos = []
    count = 0

    # Cleaning data
    # https://towardsdatascience.com/cleaning-preprocessing-text-data-for-sentiment-analysis-382a41f150d6
    global nlp
    nlp = spacy.load("en_core_web_sm")
    df = df.dropna()
    df['new_reviews'] = df['body'].apply(lambda x: " ".join(x.lower() for x in x.split()))

    df['new_reviews'] = df['new_reviews'].str.replace('[^\w\s]', '')

    df['new_reviews'] = df['new_reviews'].apply(lambda x: remove_emoji(x))
    stop = stopwords.words('english')
    df['new_reviews'] = df['new_reviews'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))
    df['new_reviews'] = df['new_reviews'].apply(space)
    df.head(20)

    for line in df.new_reviews:
        count = count + 1
        pos.append(TextBlob(line).sentiment.polarity)

        # for i in range(0,5):
        #     print(df.new_reviews[i])

    postivity = 0
    negativity = 0
    neutral = 0
    result = {}

    for i in pos:
        if i < 0:
            negativity = negativity + 1
        elif i == 0:
            neutral = neutral + 1
        else:
            postivity = postivity + 1

    # result.append([((postivity / count) * 100), ((negativity / count) * 100), ((neutral / count) * 100)])
    result["postive"] = ((postivity / count) * 100)
    result["negative"] = ((negativity / count) * 100)
    result["neutral_value"] = ((neutral / count) * 100)

    return result

# print(result)
