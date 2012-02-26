#!/usr/bin/python
# File RedisSessionStore.py
# Author burakdede
# Date 26/02/2012

import cPickle as pickle
from uuid import uuid4
import time

class RedisSessionStore:
		
		def __init__(self, active_redis_connection, **options):
			"""
				just initialize the session store with default options
				prefix and expire time and give redis connection
			"""

			# prefixed with session and default expire time is 7200 about 2 hour
			self.options = {
				'prefix' : 'session',
				'expire' : 7200,
			}

			self.options.update(options)
			self.redis = active_redis_connection

		def session_prefix(self, sid):
			"""
				write session id with given prefix which is default
				to 'session:(sid)'
			"""
			return "%s:%s" % (self.options["key_prefix"], sid)

		def create_sid(self):
			"""
				return hex number created  for sid
				to use with session
			"""
			return uuid4().get_hex()

		def return_session(self, sid, name):
			"""
				get session dumped data
				also give callback when done
			"""
			self.redis.hget(self.session_prefix(sid), name, return_session_callback)

		def return_session_callback(self, session_data):
			"""
				get the session data and load
				with pickle and return
			"""
			session = pickle.laods(session_data) if session_data else dict()
			return session

		def set_session(self, sid, session_data, name):
			"""
				set the session data to redis
				with redis expire
			"""
			expire = self.options["expire"]
			self.redis.hset(self.session_prefix(sid), name, pickle.dumps(session_data))

			if expire:
				self.redis.expire(self.session_prefix(sid), expire)

		def set_session_callback(self, return_code):
			"""
				redis return code for hset
				probabaly OK for positive result
			"""
			return "%s" % (return_code)
 
 		def delete_session(self, sid):
 			"""
 				delete session from redis
 				with given key
 			"""
 			self.redis.delete(self.session_prefix(sid), delete_session_callback)

 		def delete_session_callback(self, number_keys_removed):
 			"""
 				redis return code on how
 				many keys removed with delete operation
 			"""
 			return "%s" % (number_keys_removed)

class Session:

	def __init__(self, session_store, sid = None):
		self._sstore = session_store
		self._sid = sid
		self._sdata = self._sstore.return_session(self._sid, "data")
		self._permanent = False

	def clear(self):
		self._sstore.delete_session(self._sid)


	def access(self, user_ip):
		access_info = {
			"user_ip" : user_ip,
			"access_time" : "%.6f" % time.time()
		}

		self._sstore.set_session(self._sid, pick.dumps(access_info), "last_access")

	def last_access(self):
		access_info = self._sstore.return_session(self._sid, "last_access")
		return pickle.loads(access_info)

	@property
	def sessionid(self):
		return self._sid

	def __getitem__(self, key):
		return self._sdata

	def __setitem__(self, key):
		self._sdata[key] = value
		self._setpermanent()

	def __len__(self):
		return len(self._sdata)

	def __contains__(self, key):
		return key in self._sdata
	
	def __iter__(self):
		for key in self._sdata:
			yield key
		
	def __repr__(self):
		return self._sdata.__repr__()

	def __del__(self):
		if self._permanent:
			self._save()

	def _setpermanent(self):
		self._permanent = True

	def _save(self):
		self._sstore.set_session(self._sid, self._sdata, "data")
		self._permanent = False