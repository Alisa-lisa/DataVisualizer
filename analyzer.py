import os, re, random, ipaddress, cProfile, re, itertools
# import geoip2
# import geoip2.database as gipd
import GeoIP as gi
from multiprocessing import Pool, Manager, Process

# some helper functions
def make_readable(file):
	inF = file
	outF = os.path.splitext(inF)[0] + '.txt'
	with open(inF, 'rb') as i:
		with open(outF, 'wb') as j:
			j.write(i.read())
	os.remove(inF)
	return str(outF)

# count the number of lines in the file, the size of the file and approximate size of a line in bytes
def file_info(file):
	f = open(file)
	lines = 0
	line_size = 0
	size = os.stat(file).st_size
	for l in f:
		lines += 1
	line_size = size / lines
	f.close()
	return size, lines, line_size

# the information about this sampling can be found on https://en.wikipedia.org/wiki/Reservoir_sampling
# in our case S(n) - input file with n lines (we assume n is unknown)
# R(k) - output file called "test_filename.ext" with k lines (k is given in the parameters)
# returns teh name of the file
def reservoir_algo(input, sample_size):
	f = open(input)
	outF = 'test_' + input
	o = open(outF, 'w')
	# get a single random line:
	total_size_b = os.stat(input).st_size
	for i in range(0, sample_size):
		rand_line = random.randint(0, total_size_b)
		f.seek(rand_line)
		f.readline()
		r = f.readline()
		o.write(str(r))
	return outF

# we parse only a string, so let's use string as input parameter
## TODO: let's do only ip extraction 
def parse(s):
	new_line = []
	# clean s from delimeters
	# if re.search("( - - )", s) != None:
	# 	delimiter = re.search("( - - )", s).group(0)
	# 	s = s.replace(delimiter, " ")

	# recognize address
	r = s.split(' ')
	address = r[0]
	new_line.append(address)
	# s = s.replace(r[0], '#') 
	# get time via regex, cause simple
	# re_time = r"(\[[0-9].*[0-9]\])"
	# time = re.search(re_time, s).group(0)
	# new_line.append(time)
	# s = s.replace(time, '#')
	# # get request
	# r = s.split('"')
	# request = '"' + str(r[1]) + '"'
	# new_line.append(request)
	# s = s.replace(request, '#')
	# # get size via regex, cause ez
	# re_size = r"([0-9]{1,3} [0-9]{1,9})" 
	# size = re.search(re_size, s).group(0)
	# new_line.append(size)
	# s = s.replace(size, '#')
	# # get reference, here if suddenly stays # - means, that it was refered from own ipv4/6 (can not really happen) 
	# # here can also happen, that no agent ingo is provided, in this case we need to distinguish between "-" and "-" 
	# r = s.split('"')
	# reference = '"' + str(r[1]) + '"'
	# new_line.append(reference)
	# # here we need a check, that something is still left for agent, if not -> agent = '"-"'
	# # if there were no agent info provided, than s looks like this: '# # # # # #', it contains 6 signs '#'
	# s = s.replace(reference, '#')
	# # agent info is provided
	# if s.count('#') < 6:
	# 	# get agent normally
	# 	r = s.split('"')
	# 	agent = '"' + str(r[1]) + '"'
	# 	new_line.append(agent)
	# 	s = s.replace(agent, '#')
	# else:
	# 	agent = '"-"' 
	# 	new_line.append(agent)
	return new_line

# @profile
def get_statistics(file_name):
	f = open(file_name)
	# create reader object to determine ips origin
	ip4 = gi.open('tmp/GeoIP.dat', gi.GEOIP_STANDARD)
	ip6 = gi.open("tmp/GeoIPv6.dat", gi.GEOIP_STANDARD)
	# global results:
	false_addresses = 0 # the number of non-valid ipadresses in the log file 
	ip_by_country = {'undefined':0} # {'country':int}
	ipv4_total = 0 # total number of the ipv4
	ipv6_total = 0 # total number of the ipv6

	for line in f:
		res = parse(line)
		# validate the address, isAddress, islocal, isPrivate
		try:
			if ipaddress.ip_address(res[0]):
				if type(ipaddress.ip_address(res[0])) == ipaddress.IPv4Address:
					ipv4_total += 1
				else:
					ipv6_total += 1
				# count appereance of each ip of the country country = {'country_name':0}
				# since we use legacy GeoIP, we get 2 db for ipv4 and ipv6 -> two cases
				# ipv4 check on ipv6-db -> None (and vise versa)
				# check ipv4-db first
				if ip4.country_name_by_addr(res[0]) != None:
					origin = ip4.country_name_by_addr(res[0])
					if origin not in ip_by_country.keys():
						ip_by_country[origin] = 1
					else:
						ip_by_country[origin] += 1
				# check ipv6-db
				elif ip6.country_code_by_addr_v6(res[0]) != None:
					origin = ip6.country_name_by_addr_v6(res[0])
					if origin not in ip_by_country.keys():
						ip_by_country[origin] = 1
					else:
						ip_by_country[origin] += 1
				else:
					ip_by_country['undefined'] += 1	
				# except geoip2.errors.AddressNotFoundError:
				# 	ip_by_country['undefined'] += 1
		except ValueError:
			false_addresses += 1
	return false_addresses, ipv4_total, ipv6_total, ip_by_country

if __name__ == '__main__':
	# test = reservoir_algo('access.txt', 60000) 
	print(file_info('test_access.txt'))
	errors, ipv4, ipv6, geo = get_statistics('test_access.txt')
	print(errors, ipv4, ipv6, geo)
	print("Number of countries counted:", len(geo.keys()))
	print("undefined:", geo['undefined'])
	print("Germany:", geo['Germany'])
