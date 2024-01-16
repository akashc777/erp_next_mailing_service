# Copyright (c) 2024, Akash Hadagali and contributors
# For license information, please see license.txt
import csv
import pdfkit
import io
import zipfile
import base64
import os
import PyPDF2
from jinja2 import Template
import frappe
from frappe.model.document import Document


class GeneratePDF(Document):
	@frappe.whitelist()
	def upload_data(self):
		file = frappe.get_doc("File", {"file_url": self.upload_csv})
		html_template_data = frappe.get_doc("PDF Template", self.select_pdf_template)
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
		zip_buffer = generate_and_zip_pdfs(file.get_full_path(), html_template_data, assests)
		saved_file = self.save_file(zip_buffer.getvalue())
	
		return saved_file.file_url

	def save_file(self, zip_file_content):
		_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "generate_pdf_result.zip",
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				"is_private": False,
				"content": zip_file_content,
			}
		)
		_file.save()
		return _file

def generate_and_encrypt_pdf(html_template, row, password):
	
	html_content = []
	temp = Template(html_template.pdf_html_template).render(row)
	html_content.append(temp)
	print(temp)
	
	# check for page 2 
	if html_template.pdf_html_template_page_2:
		html_content.append(Template(html_template.pdf_html_template_page_2).render(row))
	

	# chaeck for page 3
	if html_template.pdf_html_template_page_3:
		html_content.append(Template(html_template.pdf_html_template_page_3).render(row))

	options = {'page-size': 'A4', 'enable-local-file-access': ''}
	pdf_content = pdfkit.from_string('<div style="page-break-after: always;"></div>'.join(html_content), False, options=options)

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

	return encrypted_pdf_data

def generate_and_zip_pdfs(csv_file, html_template, assests):
	zip_buffer = io.BytesIO()

	with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
		with open(csv_file, 'r', encoding='utf-8') as csv_file:
			csv_reader = csv.DictReader(csv_file)
			for row in csv_reader:
				#add assests
				row['assests'] = assests
				password = row.get('password', '')

				pdf_content = generate_and_encrypt_pdf(html_template, row, password)

				pdf_filename = f"{row['file_name']}.pdf"
				zip_file.writestr(pdf_filename, pdf_content.getvalue())

	return zip_buffer