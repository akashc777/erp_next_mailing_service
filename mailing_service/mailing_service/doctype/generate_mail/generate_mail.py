# Copyright (c) 2024, Akash Hadagali and contributors
# For license information, please see license.txt

import frappe
import pdfkit
import PyPDF2
import io
import csv
from itertools import islice
import os
from jinja2 import Template
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
import tempfile
from frappe.model.document import Document


class GenerateMail(Document):


	@frappe.whitelist()
	def send_email_with_pdf(self):
		row_no = self.row_num
		self.email_acc_doc = frappe.get_doc("Email Account", self.email_acc)
		email_pass = frappe.utils.password.get_decrypted_password(		
			self.email_acc_doc.doctype, self.email_acc_doc.name, "password", raise_exception=True
		)
		email_service = self.email_acc_doc.service
		csv_file = frappe.get_doc("File", {"file_url": self.upload_csv})
		print(self.email_acc_doc.email_server)
		print(email_service)
		print(email_pass)
		print(self.email_acc_doc.email_id)
	
		if(email_service == "Outlook.com"):
			self.mailbox = "Drafts"

		elif(email_service == "GMail"):
			self.mailbox = "[Gmail]/Drafts"

		self.mail = imaplib.IMAP4_SSL(self.email_acc_doc.email_server, 993)
		self.mail.login(self.email_acc_doc.email_id, email_pass)
		self.mail.select(self.mailbox)
		
		self.html_mail_template_data = frappe.get_doc("Mail Template", self.select_email_template)
		self.html_pdf_template_data = frappe.get_doc("PDF Template", self.select_pdf_template)
		assests = self.get_assests()
		try:
			with open(csv_file.get_full_path(), 'r', encoding='utf-8') as csv_file:
				reader = csv.DictReader(csv_file)
				for row in reader:
					row['assests'] = assests 

					self.send_email(row)
		except StopIteration:
			print("CSV file is empty or has no data.")

		self.mail.logout()

		return 

	@frappe.whitelist()
	def generate_email_preview(self):
		row_no = self.row_num
		return self.generate_email_html(row_no)

	@frappe.whitelist()
	def generate_pdf_preview(self):
		row_no = self.row_num
		html_content, _ =  self.generate_pdf_html(row_no, True)
		return html_content

	def get_assests(self):

		
		file_pdf_image_1 = frappe.get_doc("File", {"file_url": self.html_pdf_template_data.image_1})
		file_pdf_image_2 = frappe.get_doc("File", {"file_url": self.html_pdf_template_data.image_2})
		file_pdf_image_3 = frappe.get_doc("File", {"file_url": self.html_pdf_template_data.image_3})
		file_pdf_image_4 = frappe.get_doc("File", {"file_url": self.html_pdf_template_data.image_4})
		file_mail_image_1 = frappe.get_doc("File", {"file_url": self.html_mail_template_data.image_1})
		file_mail_image_2 = frappe.get_doc("File", {"file_url": self.html_mail_template_data.image_2})
		file_mail_image_3 = frappe.get_doc("File", {"file_url": self.html_mail_template_data.image_3})
		file_mail_image_4 = frappe.get_doc("File", {"file_url": self.html_mail_template_data.image_4})
		assests = {
			"mail_image_1": "http://"+file_mail_image_1.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"mail_image_2": "http://"+file_mail_image_2.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"mail_image_3": "http://"+file_mail_image_3.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"mail_image_4": "http://"+file_mail_image_4.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"pdf_image_1": "file:///" + os.path.realpath(file_pdf_image_1.get_full_path()),
			"pdf_image_2": "file:///" + os.path.realpath(file_pdf_image_2.get_full_path()),
			"pdf_image_3": "file:///" + os.path.realpath(file_pdf_image_3.get_full_path()),
			"pdf_image_4": "file:///" + os.path.realpath(file_pdf_image_4.get_full_path()),
		}

		return assests

	def send_email(self, row):
		
		pdf_html = Template(self.html_pdf_template_data.pdf_html_template).render(row)
		pdf_html_header = ''
		pdf_html_footer = ''

		if self.html_pdf_template_data.pdf_html_header:
			pdf_html_header = Template(self.html_pdf_template_data.pdf_html_header).render(row)
		
		if self.html_pdf_template_data.pdf_html_footer:
			pdf_html_footer = Template(self.html_pdf_template_data.pdf_html_footer).render(row)

		with tempfile.NamedTemporaryFile(mode='w+', delete=True) as header_file:
			header_html = '<div style="text-align: center; font-size: 12px; color: #333;">This is the header</div>'
			header_file.write(header_html)

		password = row.get('password', '')
		options = {
			'page-size': 'A4', 
			'enable-local-file-access': '',
			'header-html': header_html,
			'footer-html': pdf_html_footer, 

		}
		pdf_content = pdfkit.from_string(pdf_html,  False, options=options)

		# Encrypt PDF with the provided password
		pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
		pdf_writer = PyPDF2.PdfWriter()

		for page_num in range(len(pdf_reader.pages)):
			pdf_writer.add_page(pdf_reader.pages[page_num])

		if password:
			pdf_writer.encrypt(password)

		encrypted_pdf_data = io.BytesIO()
		pdf_writer.write(encrypted_pdf_data)
		encrypted_pdf_data.seek(0)

		email_html = Template(self.html_mail_template_data.email_html_template).render(row)
		email_msg = MIMEMultipart()
		email_msg["From"] = self.email_acc_doc.email_account_name
		email_msg["Subject"] = self.html_mail_template_data.subject
		email_msg["Date"] = formatdate(localtime=True)		
		email_msg.attach(MIMEText(email_html, "html"))

		attachment = MIMEApplication(encrypted_pdf_data.getvalue(), _subtype="pdf")  # Adjust the subtype based on your attachment type
		attachment.add_header("Content-Disposition", f"attachment; filename={row['file_name']}")
		email_msg.attach(attachment)

		recipients = row['to'].split(',')

		for recipient in recipients:
			to_add = recipient.strip()
			email_msg["To"] = to_add
			raw_message = email_msg.as_string().encode("utf-8")
			self.mail.append(self.mailbox, None, None, raw_message)

		
	def generate_email_html(self, row_no):
		csv_file = frappe.get_doc("File", {"file_url": self.upload_csv})
		html_template_data = frappe.get_doc("Mail Template", self.select_email_template)
		file_image_1 = frappe.get_doc("File", {"file_url": html_template_data.image_1})
		file_image_2 = frappe.get_doc("File", {"file_url": html_template_data.image_2})
		file_image_3 = frappe.get_doc("File", {"file_url": html_template_data.image_3})
		file_image_4 = frappe.get_doc("File", {"file_url": html_template_data.image_4})
		assests = {
			"email_image_1": "http://"+file_image_1.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"email_image_2": "http://"+file_image_2.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"email_image_3": "http://"+file_image_3.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"email_image_4": "http://"+file_image_4.get_full_path()[2:].replace("localhost", "localhost:8000"),
		}

		html_return_val = ""

		with open(csv_file.get_full_path(), 'r', encoding='utf-8') as csv_file:
			reader = csv.DictReader(csv_file)
			row = next(islice(reader, row_no-1, row_no))
			row["assests"] = assests
			
			html_return_val = Template(html_template_data.email_html_template).render(row)

		return html_return_val

	def generate_pdf_html(self, row_no, for_preview=False):
		csv_file = frappe.get_doc("File", {"file_url": self.upload_csv})
		html_template_data = frappe.get_doc("PDF Template", self.select_pdf_template)
		if not html_template_data:
			return ''
		file_image_1 = frappe.get_doc("File", {"file_url": html_template_data.image_1})
		file_image_2 = frappe.get_doc("File", {"file_url": html_template_data.image_2})
		file_image_3 = frappe.get_doc("File", {"file_url": html_template_data.image_3})
		file_image_4 = frappe.get_doc("File", {"file_url": html_template_data.image_4})
		assests = {
			"pdf_image_1": "file:///" + os.path.realpath(file_image_1.get_full_path()),
			"pdf_image_2": "file:///" + os.path.realpath(file_image_2.get_full_path()),
			"pdf_image_3": "file:///" + os.path.realpath(file_image_3.get_full_path()),
			"pdf_image_4": "file:///" + os.path.realpath(file_image_4.get_full_path()),
		}

		if for_preview:
			assests = {
				"pdf_image_1": "http://"+file_image_1.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"pdf_image_2": "http://"+file_image_2.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"pdf_image_3": "http://"+file_image_3.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"pdf_image_4": "http://"+file_image_4.get_full_path()[2:].replace("localhost", "localhost:8000"),
			}

		html_return_val = ""

		with open(csv_file.get_full_path(), 'r', encoding='utf-8') as csv_file:
			reader = csv.DictReader(csv_file)
			row = next(islice(reader, row_no-1, row_no))
			row["assests"] = assests
			html_content = Template(html_template_data.pdf_html_template).render(row)

			password = row.get('password', '')
			
			# html_return_val = '<div style="page-break-after: always;"></div>'.join(html_content)

		return html_content, password