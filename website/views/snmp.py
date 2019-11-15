import paramiko
import os, os.path, sys, socket, time
import re
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.views import View
from netaddr import IPAddress, IPNetwork
from ..models import Connect
from ..forms import NacmForm, IpFormset, UploadForm
from .. import models


class snmp(View):
	ip_list = []

	# hal yang dilakukan ketika melakukan action POST	
	def post(self, request, *args, **kwargs):
		# mengambil nilai dari form
		formm = NacmForm(request.POST)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		communitys = (request.POST.getlist('community_v2'))


		# jika form valid
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()
			collect_data = ""
			count_form = 0

			# perulangan data pada form ipform
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				collect_config = "<b>Configure on "+str(ipaddr)+" | vendor = "+str(vendor)+"</b></br>"
				networks = netmask = wildcard = ""
				# mengkoneksikan ke perangkat via protokol SSH menggunakan library Paramiko
				try:
					ssh_client = paramiko.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					# memasukkan informasi username, password SSH
					ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue,look_for_keys=False, allow_agent=False, timeout=5)
					remote_conn=ssh_client.invoke_shell()
					shell = remote_conn.recv(65535)
					config_read = str(vendor.sett_snmp)
					# split memakai \r dulu
					array_read = config_read.split('\r')
					# hasilnya akan ada \n
					output_line = ""

					# membuat perulangan pada network yang di advertise, karena pada advertise network menggunakan form dinamis
					for x in range(len(communitys)):
						community_v2 = communitys[x]
	
						# membaca code tiap line
						for line in array_read:
							# menghilangkan \n
							new_line = re.sub(r'\n','',line)
							# akan error karena ada nilai kosong dan eval tidak bisa membacanya
							# sehingga mengeleminasi nilai kosong
							if new_line != '':
								config_send = eval(new_line)
								collect_config = collect_config + config_send+"</br>" 
								print(config_send+" ini config send")
								# mengirim perintah yang akan dikonfig
								# menggunakan non-interactive shell
								try:
									stdin, stdout, stderr = ssh_client.exec_command(config_send+"\n")
									time.sleep(1)
									results = stdout.read()
									print (str(results))
								except:
									# jika gagal menggunakan interactive shell
									try:
										remote_conn.send(config_send+"\n")
										time.sleep(1)
										results = remote_conn.recv(65535)
										print (results.decode('ascii'))
									except:
										print("error paramiko")

					# menyimpan data ke sqlite
					count_form = count_form + 1	
					collect_data = collect_data + collect_config
					if count_form == len(ipform):
						simpanForm.conft = collect_data
					print (collect_config)
					messages.success(request, collect_config)
					ssh_client.close()
					
					simpanIp = form.save(commit=False)
					simpanIp.connect_id = simpanForm
					print (simpanIp)
					simpanIp.save()
					simpanForm.save()

				# jika gagal terkoneksi
				except paramiko.AuthenticationException:
					error_conf(request, collect_config, "</br>Authentication failed, please verify your credentials")
				except paramiko.SSHException as sshException:
					error_conf(request, collect_config, "</br>Could not establish SSH connection: %s" % sshException)
				except socket.timeout as e:
					error_conf(request, collect_config, "</br>Connection timed out")
				except Exception as e:
					ssh_client.close()
					error_conf(request, collect_config, "</br>Exception in connecting to the server: %s" % e)

		return HttpResponseRedirect('snmp')
	
	# hal yang dilakukan ketika melakukan action GET
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/snmp.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform})


def error_conf(request, collect_config, error1):
	conf_error = collect_config+error1
	messages.error(request, conf_error)
	result_flag = False


