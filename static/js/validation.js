function validateUserForm() {
	var title = $("#title").val();
	var initials = $("#initials").val();
	var name = $("#name").val();
	var surname = $("#surname").val();
	var email = $("#email").val();
	var cell = $("#cell").val();
	var user_id = $("#user_id").val();
	var acc_type = $("#acc_type").val();
	var quota = $("#quota").val();

	if(title == null || title == "" ||
		initials == null || initials == "" ||
		name == null || name == "" ||
		surname == null || surname == "" ||
		email == null || email == "" ||
		cell == null || cell == "" ||
		user_id == null || user_id == "" ||
		acc_type == null || acc_type == "" ||
		quota == null || quota == "") {
		alert("Please fill in all fields");
		return false;
	}

	if(password != passwordConfirm) {
		alert("Passwords do not correspond");
		return false;
	}

	if(acc_type != 'A' && acc_type != 'a' && acc_type != 'U' && acc_type != 'u') {
		alert("Please select a valid acc_type");
		return false;
	}
	
	if(user_id.length < 8 || user_id.length > 8) {
		alert("Invalid user ID length");
		return false;
	}

	for(var i = 0; i < user_id.length; ++i) {
		if(isNaN(user_id[i])) {
			alert("Please enter a valid user ID");
			return false;
		}
	}
	
	if(cell.length < 10 || cell.length > 10) {
		alert("Invalid cell number length");
		return false;
	}	

	for(var j = 0; j < cell.length; ++j) {
		if(isNaN(cell[j])) {
			alert("Please enter a valid cell number");
			return false;
		}
	}

	if(isNaN(quota)) {
		alert("Please enter a valid disk quota in megabytes");
		return false;
	}

	return true; // Data valid
}