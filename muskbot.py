from textblob import TextBlob
import configparser
import tweepy


# Read 'conf.ini' file to get twitter API credentials and other constants
parser = configparser.ConfigParser()
parser.read('conf.ini')

API_KEY = parser.get('twitter_credentials', 'api_key')
API_KEY_SECRET = parser.get('twitter_credentials', 'api_key_secret')
ACCESS_TOKEN = parser.get('twitter_credentials', 'access_token')
ACCESS_TOKEN_SECRET = parser.get('twitter_credentials', 'access_token_secret')

FOLLOWED_USERS = [id for _, id in parser.items('followed_users')]

TRACKED_COINS = {
    textInTweet:binancePair for binancePair, textsInTweet in parser.items('coins') for textInTweet in textsInTweet.split(', ')
}

NEGATIVES_WORDS = {
    word:polarity for word, polarity in parser.items('negative_words')
}


# OAuth with Twitter API
auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


# Streaming for listening to tweets
class TweetStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        # Skip tweets that are not posted by any of the followed users (replies, retweets from other users ..)
        if status.user.id_str not in FOLLOWED_USERS:
            return

        if (self.check_tweet_for_coins(status.text)):
            print(status.text)

            # Sentiment analysis => only buy if the sentence is positive
            if (self.is_positive_sentence(status.text)):
                print('positive')
            else:
                print('negative')

    def check_tweet_for_coins(_, tweet):
        return any(coin in tweet.lower() for coin in list(TRACKED_COINS.keys()))

    def is_positive_sentence(_, sentence:str) -> bool:
        analysis = TextBlob(sentence)
        custom_polarity = 0

        for word in sentence.split(' '):
            if (word.lower() in NEGATIVES_WORDS):
                custom_polarity += int(NEGATIVES_WORDS[word])

        return analysis.sentiment.polarity - custom_polarity >= 0


# Start the stream
tweetStreamListener = TweetStreamListener()
tweetStream = tweepy.Stream(auth=api.auth, listener=tweetStreamListener)

tweetStream.filter(follow=FOLLOWED_USERS, is_async=True)