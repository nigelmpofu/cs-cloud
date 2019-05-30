// Call this function with the jQuery object representing the
// DOM element from which to start searching for the user's fields
function editUserHookUpdateButtons(jQueryObject) {
	jQueryObject.find(".edit").on("click", function () {
		var pk = $(this).data("pk");
		$("#more").attr("data-pk", pk);
		var token = $(this).data("csrf");
		var row = $("#user" + pk);

		var user_id = row.find("[data-id='user_id']");
		var title = row.find("[data-id='title']");
		var initials = row.find("[data-id='initials']");
		var fname = row.find("[data-id='fname']");
		var surname = row.find("[data-id='surname']");
		var email = row.find("[data-id='email']");
		var cellp = row.find("[data-id='cell']");
		var acc_type = row.find("[data-id='acc_type']");
		var quota = row.find("[data-id='quota']");

		$("#e_user_id").val(user_id.text());
		$("#e_title").val(title.text());
		$("#e_initials").val(initials.text());
		$("#e_fname").val(fname.text());
		$("#e_surname").val(surname.text());
		$("#e_email").val(email.text());
		$("#e_cell").val(cellp.text());
		//$("#e_acc_type").val(acc_type.text() === true);
		$("#e_quota").val(parseInt(quota.text()));

		// For password reset form
		$("#p_user_id").val(user_id.text());

		var e_acc_type = $("#e_acc_type");
		if(acc_type.text() == "True") {
			e_acc_type.val("Admin");
		} else {
			e_acc_type.val("User");
		}
		
		if(!isAdmin) {
			e_acc_type.prop("disabled", true);
		}/* else if(userPK == pk) {
			$("#resetPassword").show();
		} else {
			$("#resetPassword").hide();
		}*/

		$("#updateConfirm").unbind('click').on("click", function () {
			var user_acc_type = false;

			if(e_acc_type.val() == "Admin") {
				user_acc_type = true; // Admin
			} else {
				user_acc_type = false; // Not admin
			}

			var data = {
				'user_id': $("#e_user_id").val(),
				'title': $("#e_title").val(),
				'initials': $("#e_initials").val(),
				'name': $("#e_fname").val(),
				'surname': $("#e_surname").val(),				
				'email': $("#e_email").val(),
				'cell': $("#e_cell").val(),
				'quota': (parseInt($("#e_quota").val()) * 1024 * 1024),
				'acc_type': user_acc_type,
				'csrfmiddlewaretoken': token
			};

			$.ajax({
				type: 'POST',
				url: '/admin/userAdmin/editUser/',
				data: data,
				success: function () {
					user_id.text($("#e_user_id").val());
					title.text($("#e_title").val());
					initials.text($("#e_initials").val());
					fname.text($("#e_fname").val());
					surname.text($("#e_surname").val());
					cellp.text($("#e_cell").val());
					email.text($("#e_email").val());
					quota.text($("#e_quota").val());
					acc_type.text(user_acc_type);
				}
			});
		});
	});
};