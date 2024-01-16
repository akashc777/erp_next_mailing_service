// Copyright (c) 2024, Akash Hadagali and contributors
// For license information, please see license.txt

frappe.ui.form.on("Generate Mail", {
	get_pdf_preview: function(frm) {
        frm.call({
            method: 'generate_pdf_preview',
            doc: frm.doc,
            freeze: true,
            freeze_message: __('Generating Preview'),
            callback: function(r) {
                console.log(r)
                if (r && r.message) {
                    let content = r.message;
                    let opts = {
                        title: "Preview",
                        subtitle: "preview",
                        content: content,
                        print_settings: {orientation: "landscape"},
                        columns: [],
                        data: [],
                    }
                    frappe.render_grid(opts);
                }
            }
        })
    },
    get_email_preview: function(frm) {
        frm.call({
            method: 'generate_email_preview',
            doc: frm.doc,
            freeze: true,
            freeze_message: __('Generating Preview'),
            callback: function(r) {
                console.log(r)
                if (r && r.message) {
                    let content = r.message;
                    let opts = {
                        title: "Preview",
                        subtitle: "preview",
                        content: content,
                        print_settings: {orientation: "landscape"},
                        columns: [],
                        data: [],
                    }
                    frappe.render_grid(opts);
                }
            }
        })
    },
    send_mail: function(frm) {
        frm.call({
            doc: frm.doc,
            method:"send_email_with_pdf",
            freeze:true,
            freeze_message:"enquing mail ...",
            callback:function(r){
                console.log(r)
            }
        })
    }
});
