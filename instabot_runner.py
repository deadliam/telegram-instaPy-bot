
import json
import sys
import time
from instapy import InstaPy

working_dir = "/home/pi/Instagram"

def readConfig():
	with open(working_dir + '/config.json', 'r') as myfile:
		data=myfile.read()
		obj = json.loads(data)
		return obj['accounts']


def startBot(account):
	
	session = InstaPy(username=account["username"], password=account["password"], headless_browser=True)
	session.login()

	session.set_dont_like(["naked", "nsfw"])
	#session.set_do_follow(True, percentage=50)
	session.set_do_follow(enabled=False, percentage=50)
	session.set_do_comment(True, percentage=100)
	session.set_comments(account["comments"])
	session.set_skip_users(skip_private=True,
					   private_percentage=100,
					   skip_business=True,
					   skip_non_business=False,
					   business_percentage=100)
	session.set_relationship_bounds(enabled=True, max_followers=1000)

	# This line should be at the very end
	
	if account["locations"][0] != "":
		session.new_like_by_locations(locations=account["locations"], amount=account["likes_amount"], media=None, randomize=False, skip_top_posts=False, like_amount_per_user=2)
	else:
		session.like_by_tags(account["tags"], amount=account["likes_amount"])

	session.end()


if __name__ == "__main__":
	
	accounts = readConfig()

	if sys.argv[1] != "":
		accountName = sys.argv[1]
		for account in accounts:
			if account["username"] == accountName:
				startBot(account)
				break
			
	else:
		for account in accounts:
			startBot(account)


""" Quickstart script for InstaPy usage """
# imports
# from instapy import InstaPy
# from instapy import smart_run

# # login credentials
# insta_username = 'ellis_from_los'  # <- enter username here
# insta_password = 'Ellisfromlos1'  # <- enter password here

# # get an InstaPy session!
# # set headless_browser=True to run InstaPy in the background
# session = InstaPy(username=insta_username,
#                   password=insta_password,
#                   headless_browser=False)

# with smart_run(session):
#     """ Activity flow """
#     # general settings
#     session.set_relationship_bounds(enabled=True,
#                                     delimit_by_numbers=True,
#                                     max_followers=4590,
#                                     min_followers=45,
#                                     min_following=77)

#     session.set_dont_include(["friend1", "friend2", "friend3"])
#     session.set_dont_like(["pizza", "#store"])

#     # activity
#     session.like_by_tags(["natgeo"], amount=10)

