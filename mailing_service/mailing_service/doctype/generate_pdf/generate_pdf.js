// Copyright (c) 2024, Akash Hadagali and contributors
// For license information, please see license.txt

frappe.ui.form.on("Generate PDF", {
	upload: function(frm) {
        frm.call({
            doc: frm.doc,
            method:"upload_data",
            freeze:true,
            freeze_message:"Data Uploading ...",
            callback:function(r){
                console.log(r)
                frm.reload_doc();
                if(r.message) {
                    open_url_post(frappe.request.url, {
                        cmd: 'frappe.core.doctype.file.file.download_file',
                        file_url: r.message
                    });
                }
            }
        })
    }
});
