from binance_api import API_KEY, API_KEY_SECRET, BinanceApi
from textblob import TextBlob
from binance.client import Client
from binance.enums import SIDE_BUY, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC
from binance.exceptions import BinanceAPIException
import configparser
import tweepy


# Read 'conf.ini' file to get twitter API credentials and other constants
parser = configparser.ConfigParser()
parser.read('conf.ini')

TWITTER_API_KEY = parser.get('twitter_credentials', 'api_key')
TWITTER_API_KEY_SECRET = parser.get('twitter_credentials', 'api_key_secret')
ACCESS_TOKEN = parser.get('twitter_credentials', 'access_token')
ACCESS_TOKEN_SECRET = parser.get('twitter_credentials', 'access_token_secret')

BINANCE_API_KEY = parser.get('binance_credentials', 'api_key')
BINANCE_API_KEY_SECRET = parser.get('binance_credentials', 'api_key_secret')

FOLLOWED_USERS = [id for _, id in parser.items('followed_users')]

TRACKED_COINS = {
    text_in_tweet: binance_pair for binance_pair, text_in_tweet in parser.items('coins')
    for text_in_tweet in text_in_tweet.split(', ')
}

NEGATIVES_WORDS = {
    word: polarity for word, polarity in parser.items('negative_words')
}


# OAuth with Twitter API
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

# OAuth with Binance API
binance_api = BinanceApi(API_KEY, API_KEY_SECRET)


# Streaming for listening to tweets
def check_sentence_for_coins(sentence: str) -> bool:
    """Returns true if a string contains any words refering to a followed coins

    Args:
        sentence (str): the sentence

    Returns:
        bool: true if the sentence contains a coin
    """
    return any(word in sentence.lower() for word in list(TRACKED_COINS.keys()))


def is_positive_sentence(sentence: str) -> bool:
    """Returns true if the sentence is mainly positive

    Args:
        sentence (str): the sentence

    Returns:
        bool: true if the sentence is mainly positive
    """
    analysis = TextBlob(sentence)
    custom_polarity = 0

    for word in sentence.split(' '):
        if word.lower() in NEGATIVES_WORDS:
            custom_polarity += int(NEGATIVES_WORDS[word])

    return analysis.sentiment.polarity - custom_polarity >= 0


class TweetStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        # Skip tweets that are not posted by any of the followed users (replies, retweets from other users ..)
        if status.user.id_str not in FOLLOWED_USERS:
            return

        if check_sentence_for_coins(status.text):
            print(status.text)

            # Sentiment analysis => only buy if the sentence is positive
            if is_positive_sentence(status.text):
                # TODO BUY HERE
                print('positive')
            else:
                print('negative')


# Start the stream
tweetStreamListener = TweetStreamListener()
tweetStream = tweepy.Stream(auth=twitter_api.auth, listener=tweetStreamListener)

tweetStream.filter(follow=FOLLOWED_USERS, is_async=True)
