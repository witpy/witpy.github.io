import pymongo
import json
import operator
import math
import matplotlib.pyplot as plt
import requests


def download_file(filename):
	file = filename
	url = 'https://wikitalkpages.s3.ap-south-1.amazonaws.com/' + file +'.json'
	r = requests.get(url, allow_redirects=True)
	open(file + '.json', 'wb').write(r.content)



def putInDatabase(collection_name, file_name, myclient, mongoClientDB):
	collection = mongoClientDB[collection_name]
	json_file = open(file_name)
	data = json_file.read().strip("[]").split("\"},")
	for i in range(len(data)):
		if i != len(data)-1:
			data[i] += "\"}"
		ins = json.loads(data[i])
		collection.insert(ins)


class Analyzer:



	def __init__(self, myclient, mongoClientDB):
		self.myclient = myclient
		self.mongoClientDB = mongoClientDB
		self.dataCollectionName = None


	def download_file(self, filename):
		file = filename
		url = 'https://wikitalkpages.s3.ap-south-1.amazonaws.com/' + file +'.json'
		r = requests.get(url, allow_redirects=True)
		json_file = file + '.json'
		open(filename, 'wb').write(r.content)


	def putInDatabase(self, collection_name, file_name):
		collection = self.mongoClientDB[collection_name]
		json_file = open(file_name)
		data = json_file.read().strip("[]").split("\"},")
		for i in range(len(data)):
			if i != len(data)-1:
				data[i] += "\"}"
			ins = json.loads(data[i])
			collection.insert(ins)


	def deleteCollection(self, collection_name):
		collection = self.mongoClientDB[collection_name]
		collection.drop()



	def downloadAndLoad(self, collection_name, filename):
		self.download_file(filename)
		self.putInDatabase(collection_name, filename)


	def setCollectionName(self, dataCollectionName):
		self.dataCollectionName = dataCollectionName



	def getAlldata(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		arr = []
		for x in mycol.find():
		 	arr.append(x)
		return arr



	def totalNumberOfComments(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		return mycol.count()



	def getAllAuthors(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		return mycol.distinct('user')



	def allAuthorsContribution(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		pipeline = {"$group":{"_id":"$user", "count":{"$sum":1}}}
		dictionary = mycol.aggregate([pipeline])
		answer = {}
		for item in dictionary:
			answer[item["_id"]] = item["count"]
		return answer



	def getTopNContributors(self, n):
		authors = self.allAuthorsContribution()
		sorted_d = dict(sorted(authors.items(), key=operator.itemgetter(1),reverse=True))
		new_dict = {}
		num = 0
		for key, val in sorted_d.items():
			if num == n:
				break
			num += 1
			new_dict[key] = val
		return new_dict



	def getLeastNContributors(self, n):
		authors = self.allAuthorsContribution()
		sorted_d = dict(sorted(authors.items(), key=operator.itemgetter(1),reverse=False))
		new_dict = {}
		num = 0
		for key, val in sorted_d.items():
			if num == n:
				break
			num += 1
			new_dict[key] = val
		return new_dict



	def allCommentStatistics(self):
		dictionary = {}
		min_len = 999999999999999 # Done
		max_len = 0 # Done
		avg = 0  # Done
		totalLen = 0  # Done
		standardDev = 0 # Done
		count = 0  # Done
		variance = 0 # Done

		all_data = self.getAlldata()

		for item in all_data:
			count += 1
			x = len(item['text'])
			if x < min_len:
				min_len = x
			if x > max_len:
				max_len = x
			totalLen += x
		
		avg = float(totalLen) / float(count)
		value = 0
		for item in all_data:
			x = len(item['text'])
			value += (x - avg) * (x - avg)
		variance = float(value) / float(count)
		standardDev = math.sqrt(variance)

		dictionary['min_len'] = min_len
		dictionary['max_len'] = max_len
		dictionary['avg'] = avg
		dictionary['totalLen'] = totalLen
		dictionary['standardDev'] = standardDev
		dictionary['count'] = count
		dictionary['variance'] = variance
		return dictionary



	def showCommentsStatistics(self, numBucket):
		dictionary = self.allCommentStatistics()
		numberOfBuckets = float(numBucket)
		bucketLength = float(dictionary['max_len'] - dictionary['min_len']) / numBucket
		blocks = [0 for k in range(numBucket+1)]
		all_data = self.getAlldata()
		min_len = dictionary['min_len']

		for item in all_data:
			x = len(item['text'])
			blocks[int((x - min_len)/bucketLength)] += 1

		plt.xlabel('Length of comment')
		plt.ylabel('Comment Length Frequency')

		plt.bar([i+1 for i in range(numBucket+1)], blocks, width=0.8, bottom=None, align='center')
		plt.show()



	def getAllRevisionIds(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		return mycol.distinct('revision_id')



	def commentDictionaryRevisionId(self):
		rev_id = self.getAllRevisionIds()
		dictionary = {}

		for item in rev_id:
			dictionary[item] = []
		all_data = self.getAlldata()

		for item in all_data:
			dictionary[item['revision_id']].append(item)

		return dictionary



	def commentCountByRevisionId(self):
		dictionary = self.commentDictionaryRevisionId()
		for key, val in dictionary.items():
			dictionary[key] = len(val)
		return dictionary



	def getTopNRevisions(self, n):
		authors = self.commentCountByRevisionId()
		sorted_d = dict(sorted(authors.items(), key=operator.itemgetter(1),reverse=True))
		new_dict = {}
		num = 0
		for key, val in sorted_d.items():
			if num == n:
				break
			num += 1
			new_dict[key] = val
		return new_dict



	def getLeastNRevisions(self, n):
		authors = self.commentCountByRevisionId()
		sorted_d = dict(sorted(authors.items(), key=operator.itemgetter(1),reverse=False))
		new_dict = {}
		num = 0
		for key, val in sorted_d.items():
			if num == n:
				break
			num += 1
			new_dict[key] = val
		return new_dict



	def commentsFilterByRevisionId(self, revisionId):
		mycol = self.mongoClientDB[self.dataCollectionName]
		rev_id_comments = mycol.find({"revision_id": revisionId})
		return list(rev_id_comments)



	def getDepthOfCommentsInRevision(self, revisionId):
		arr = self.commentsFilterByRevisionId(revisionId)
		dictionary = {}

		for item in arr:
			dictionary[item['id']] = item['parent_id']

		keys = list(dictionary.keys())
		depth_dict = {}

		for key, val in dictionary.items():
			depth_dict[key] = 1

		for item in keys:
			it = item
			while dictionary[it] != 0:
				depth_dict[item] += 1
				it = dictionary[it]
		return depth_dict



	def getDepthOfComment(self, id, revisionId):
		arr = self.commentsFilterByRevisionId(revisionId)
		dictionary = {}

		for item in arr:
			dictionary[item['id']] = item['parent_id']

		keys = list(dictionary.keys())
		depth_dict = {}

		for key, val in dictionary.items():
			depth_dict[key] = 1

		for item in keys:
			it = item
			while dictionary[it] != 0:
				depth_dict[item] += 1
				it = dictionary[it]
		print(depth_dict)
		return depth_dict[id]



	def depthStatisticsByRevisionId(self, revisionId):
		dictionary = self.getDepthOfCommentsInRevision(revisionId)
		arr = []

		for key, val in dictionary.items():
			arr.append(val)

		dictionary = {}
		min_len = 999999999999999 # Done
		max_len = 0 # Done
		avg = 0  # Done
		totalLen = 0  # Done
		standardDev = 0 # Done
		count = len(arr)  # Done
		variance = 0 # Done

		for item in arr:
			if item < min_len:
				min_len = item
			if item > max_len:
				max_len = item
			totalLen += item

		avg = float(totalLen) / float(count)

		for item in arr:
			variance += (item - avg) * (item - avg)

		variance = float(variance) / float(count)
		standardDev = math.sqrt(variance)

		dictionary['min_len'] = min_len
		dictionary['max_len'] = max_len
		dictionary['avg'] = avg
		dictionary['standardDev'] = standardDev
		dictionary['count'] = count
		dictionary['variance'] = variance
		return dictionary



	def getAllSections(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		return mycol.distinct('section')



	def commentsFilterBySection(self, sectionName):
		mycol = self.mongoClientDB[self.dataCollectionName]
		return list(mycol.find({"section":sectionName}))



	def getSectionwiseCommentCount(self):
		mycol = self.mongoClientDB[self.dataCollectionName]
		pipeline = {"$group":{"_id":"$section", "count":{"$sum":1}}}
		dictionary = mycol.aggregate([pipeline])
		answer = {}
		for item in dictionary:
			answer[item["_id"]] = item["count"]
		return answer



	def showSectionsStatistics(self):
		dictionary = self.getSectionwiseCommentCount()
		
		arr = []
		for key, val in dictionary.items():
			arr.append(val)

		dictionary = {}
		min_len = 999999999999999 # Done
		max_len = 0 # Done
		avg = 0  # Done
		totalLen = 0  # Done
		standardDev = 0 # Done
		count = len(arr)  # Done
		variance = 0 # Done

		for item in arr:
			if item < min_len:
				min_len = item
			if item > max_len:
				max_len = item
			totalLen += item

		avg = float(totalLen) / float(count)

		for item in arr:
			variance += (item - avg) * (item - avg)

		variance = float(variance) / float(count)
		standardDev = math.sqrt(variance)

		dictionary['min_len'] = min_len
		dictionary['max_len'] = max_len
		dictionary['avg'] = avg
		dictionary['standardDev'] = standardDev
		dictionary['count'] = count
		dictionary['variance'] = variance
		return dictionary



if __name__ == '__main__':

	myclient = pymongo.MongoClient("mongodb://localhost:27017/")
	mongoClientDB = myclient['mywikidump']

	analyzer = Analyzer(myclient, mongoClientDB)

	analyzer.downloadAndLoad('Indian_Institute_of_Technology_Ropar', 'Indian_Institute_of_Technology_Ropar')

	"""
	analyzer.deleteCollection('Indian_Institute_of_Technology_Ropar')
	analyzer.deleteCollection('Animal')
	analyzer.deleteCollection('Taj_Mahal')
	analyzer.deleteCollection('United_States')
	analyzer.deleteCollection('World_Wide_Web')
	analyzer.deleteCollection('mywikicollection')
	"""


	#analyzer.setCollectionName('Animal')
	#analyzer.setCollectionName('Taj_Mahal')
	#analyzer.setCollectionName('Indian_Institute_of_Technology_Ropar')
	#analyzer.setCollectionName('United_States')
	#analyzer.setCollectionName('World_Wide_Web')




	#print(analyzer.getAlldata())
	#print(analyzer.totalNumberOfComments())
	#print(analyzer.getAllAuthors())
	#print(analyzer.allAuthorsContribution())
	#print(analyzer.getTopNContributors(7))
	#print(analyzer.getLeastNContributors(7))
	#print(analyzer.allCommentStatistics())
	#analyzer.showCommentsStatistics(100)
	#print(analyzer.getAllRevisionIds())
	#print(analyzer.commentDictionaryRevisionId())
	#print(analyzer.commentCountByRevisionId())
	#print(analyzer.getTopNRevisions(7))
	#print(analyzer.getLeastNRevisions(7))
	#print(analyzer.commentsFilterByRevisionId('99947940'))
	#print(analyzer.getDepthOfCommentsInRevision('99947940'))
	#print(analyzer.getDepthOfComment(15, '99947940'))
	#print(analyzer.depthStatisticsByRevisionId('99947940'))
	#print(analyzer.getAllSections())
	#print(analyzer.commentsFilterBySection('Disputed origins, doubtful sourcing approach'))
	#print(analyzer.getSectionwiseCommentCount())
	#print(analyzer.showSectionsStatistics())






### Write Statistics in File

"""
if __name__ == '__main__':
	myclient = pymongo.MongoClient("mongodb://localhost:27017/")
	mongoClientDB = myclient['mywikidump']

	dataCollectionName = 'Animal'

	#getDepthOfComment('Animal', myclient, mongoClientDB, 100)
	print(getDepthOfComment(dataCollectionName, myclient, mongoClientDB, 17, '41691344'))
	#print(len(commentsFilterByRevisionId(dataCollectionName, myclient, mongoClientDB, )))

	#dict_ = commentDictionaryRevisionId(dataCollectionName, myclient, mongoClientDB)

	for key, val in dict_.items():
		print(key, val)
		print("\n\n\n")

	#arr = getAlldata('Animal', myclient, mongoClientDB)

	#print(getAllAuthors('Animal', myclient, mongoClientDB))

	#dic = allCommentStatistics('Animal', myclient, mongoClientDB)

	#print(dic)

	#showCommentsStatistics('Animal', myclient, mongoClientDB, 150)

	for item in arr:
		print(item)
		print("\n\n")

	#print(myclient.list_database_names())

	#putInDatabase('Indian_Institute_of_Technology_Ropar', 'Indian_Institute_of_Technology_Ropar.json', myclient, mongoClientDB)
	#putInDatabase('Animal', 'Animal.json', myclient, mongoClientDB)
	#putInDatabase('Taj_Mahal', 'Taj_Mahal.json', myclient, mongoClientDB)
	#putInDatabase('United_States', 'United_States.json', myclient, mongoClientDB)
	#putInDatabase('World_Wide_Web', 'World_Wide_Web.json', myclient, mongoClientDB)



"""
