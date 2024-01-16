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
from frappe.model.document import Document


class GenerateMail(Document):


	@frappe.whitelist()
	def send_email_with_pdf(self):
		row_no = self.row_num
		return self.send_email(row_no)

	@frappe.whitelist()
	def generate_email_preview(self):
		row_no = self.row_num
		return self.generate_email_html(row_no)

	@frappe.whitelist()
	def generate_pdf_preview(self):
		row_no = self.row_num
		html_content, _ =  self.generate_pdf_html(row_no, True)
		return html_content

	def send_email(self, row):
		email_html = self.generate_email_html(row)
		pdf_html, password =  self.generate_pdf_html(row)

		options = {'page-size': 'A4', 'enable-local-file-access': ''}
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
		email_args = {
			'recipients': ['akashc777@gmail.com', 'akashct1999@gmail.com'],
			'message' : email_html,
			'subject' : "boom baam",
			'reference_name' : self.name,
			'reference_doctype' : self.doctype,
			'attachments': [{
				'fname': 'boom_boom.pdf',
				'fcontent': encrypted_pdf_data.read()
			}],
			"now": "True"
		}

		a = frappe.enqueue(method=frappe.sendmail, queue='short', timeout=300, **email_args)
		print(a)

		
	def generate_email_html(self, row_no):
		csv_file = frappe.get_doc("File", {"file_url": self.upload_csv})
		html_template_data = frappe.get_doc("Mail Template", self.select_email_template)
		file_image_1 = frappe.get_doc("File", {"file_url": html_template_data.image_1})
		file_image_2 = frappe.get_doc("File", {"file_url": html_template_data.image_2})
		file_image_3 = frappe.get_doc("File", {"file_url": html_template_data.image_3})
		file_image_4 = frappe.get_doc("File", {"file_url": html_template_data.image_4})
		assests = {
			"image_1": "http://"+file_image_1.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"image_2": "http://"+file_image_2.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"image_3": "http://"+file_image_3.get_full_path()[2:].replace("localhost", "localhost:8000"),
			"image_4": "http://"+file_image_4.get_full_path()[2:].replace("localhost", "localhost:8000"),
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
			"image_1": "file:///" + os.path.realpath(file_image_1.get_full_path()),
			"image_2": "file:///" + os.path.realpath(file_image_2.get_full_path()),
			"image_3": "file:///" + os.path.realpath(file_image_3.get_full_path()),
			"image_4": "file:///" + os.path.realpath(file_image_4.get_full_path()),
		}

		if for_preview:
			assests = {
				"image_1": "http://"+file_image_1.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"image_2": "http://"+file_image_2.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"image_3": "http://"+file_image_3.get_full_path()[2:].replace("localhost", "localhost:8000"),
				"image_4": "http://"+file_image_4.get_full_path()[2:].replace("localhost", "localhost:8000"),
			}

		html_return_val = ""

		with open(csv_file.get_full_path(), 'r', encoding='utf-8') as csv_file:
			reader = csv.DictReader(csv_file)
			row = next(islice(reader, row_no-1, row_no))
			row["assests"] = assests
			html_content = []
			html_content.append(Template(html_template_data.pdf_html_template).render(row))

			password = row.get('password', '')
			
			# check for page 2 
			if html_template_data.pdf_html_template_page_2:
				html_content.append(Template(html_template_data.pdf_html_template_page_2).render(row))
			

			# chaeck for page 3
			if html_template_data.pdf_html_template_page_3:
				html_content.append(Template(html_template_data.pdf_html_template_page_3).render(row))

			html_return_val = '<div style="page-break-after: always;"></div>'.join(html_content)

		return html_return_val, password