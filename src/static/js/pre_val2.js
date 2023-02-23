$(document).ready(function() { 
 
	
	var device_select = document.getElementById('device_select');
	var age_select = document.getElementById('age_select');
	var cohort_select = document.getElementById('cohort_select');
	var gender_select = document.getElementById('gender_select');
	var user_select = document.getElementById('user_select');
	var selected_device, selected_user,selected_age,selected_gender,selected_cohort;
	$('.group_data').hide()

    const picker = new Litepicker({ 
		element: document.getElementById('date_select_tab_2'),
		singleMode: false,
		allowRepick: true 
	});

    function get_group_data(){
		$('.loading').show();
		$.ajax({
			type:"GET",
			url: "/pre_val2_group_data",
			data: {
				selected_device: selected_device,
				selected_cohort :selected_cohort,
				selected_age : selected_age,
				selected_gender : selected_gender,
			},
			success: function(data){
			   update_group_difference_table(data);
			   $('.loading').hide();
			},
			error: function (error) {
				if(error?.responseJSON?.data?.login_required){
					location.href = "/";
					localStorage.setItem("SESSION_EXP", true);
				}
				show_err_message('night_option');
				$('.loading').hide();
			}
		})

	}

	function get_individual_data(start_date, end_date) {
		$('.loading').show();
		$('.err_block').hide();
		$('.group_data').hide();

		$.ajax({
			type:"GET",
			url: "/pre_val2_individual_data",
			data: {
				selected_user: selected_user,
                start_date: start_date,
		        end_date: end_date,
			},
			success: function(data){
			    $('.loading').hide();
				$('.group_data').show();	
				// update_patient_details(data.user_details)
				if(data.apple_diff) update_individual_apple_difference_table(data.apple_diff)
				if(data.fitbit_diff)update_individual_fitbit_difference_table(data.fitbit_diff)
				if(data.apple_statics)update_apple_statics_table(data.apple_statics)
				if(data.fitbit_statics)update_fitbit_statics_table(data.fitbit_statics)
				if(data.circadian_rhythms_apple_graphJSON){
					var apple_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_apple_graphJSON);
					Plotly.newPlot("apple_circadian_rhythms", apple_circadian_rhythms_graphJSON.data, apple_circadian_rhythms_graphJSON.layout);
				    
				}
				if(data.circadian_rhythms_fitbit_graphJSON){
					var fitbit_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_fitbit_graphJSON);
				    Plotly.newPlot("fitbit_circadian_rhythms", fitbit_circadian_rhythms_graphJSON.data, fitbit_circadian_rhythms_graphJSON.layout);
				}
				
				
				// update_quality_issues(data.quality_issues)
				update_user_qa_ans(data.user_que_ans)

			},
			error: function (error) {
				if(error?.responseJSON?.data?.login_required){
					location.href = "/";
					localStorage.setItem("SESSION_EXP", true);
				}
				$('.loading').hide();
				$('.err_individual').show();
			}
		})

	}

	function update_statics_table(table_data){
		var html_tbody = '';
		$.each(table_data, function(index, value){  
			var label_and_val_max = format_metrics_lable_and_value(value.Metric , value.max)
			var label_and_val_min = format_metrics_lable_and_value(value.Metric , value.min)
			var label_and_val_mean = format_metrics_lable_and_value(value.Metric , value.mean)
			html_tbody += '<tr>';
			html_tbody += `<td>${label_and_val_max.lable}</td><td>${label_and_val_max.value}</td><td>${label_and_val_min.value}</td>
			<td>${label_and_val_mean.value}</td>`
			html_tbody += '<tr>';
		});
		$('#statics_table_body').html(html_tbody);
	}

	function update_user_qa_ans(data){
		var ins_sel = $('.pre_val_1_insomnia_test ul');
		var sleep_apnea_sel = $('.pre_val_1_sleep_apnea_test ul');
		var eds_sel = $('.pre_val_1_eds_test ul');
		var cr_sel = $('.pre_val_1_rme_test ul');
		show_patient_question_ans(data, ins_sel,sleep_apnea_sel, eds_sel, cr_sel)
	}

	function update_group_difference_table(data){
		var html_tbody = ''
		json_data = JSON.parse(data.replace(/\bNaN\b/g, "null"));
		for (var [key, value] of Object.entries(json_data)) {
			html_tbody += '<tr>';
			html_tbody += `<td>${key}</td><td>${value.BedTime_Diff}</td><td>${value.SleepOnset_Diff}</td>
			<td>${value.SleepOffSet_Diff}</td><td>${value.OutOfBed_Diff}</td>`
			html_tbody += '</tr>';
		}
		$('#statics_table_group_body').html(html_tbody);
	}
	function update_individual_apple_difference_table(data){
		var html_tbody = ''
		json_data = JSON.parse(data.replace(/\bNaN\b/g, "null"));
		for (var [key, value] of Object.entries(json_data)) {
			html_tbody += '<tr>';
			html_tbody += `<td>${key}</td><td>${value.BedTime_Diff}</td><td>${value.SleepOnset_Diff}</td>
			<td>${value.SleepOffSet_Diff}</td><td>${value.OutOfBed_Diff}</td>`
			html_tbody += '</tr>';
		}
		$('#statics_table_apple_body').html(html_tbody);
	}
	function update_individual_fitbit_difference_table(data){
		var html_tbody = ''
		json_data = JSON.parse(data.replace(/\bNaN\b/g, "null"));
		for (var [key, value] of Object.entries(json_data)) {
			html_tbody += '<tr>';
			html_tbody += `<td>${key}</td><td>${value.BedTime_Diff}</td><td>${value.SleepOnset_Diff}</td>
			<td>${value.SleepOffSet_Diff}</td><td>${value.OutOfBed_Diff}</td>`
			html_tbody += '</tr>';
		}
		$('#statics_table_fitbit_body').html(html_tbody);
	}

	function update_apple_statics_table(data) {
		var html_header = `<tr><th>Metrics</th><th >Max</th><th >Min</th><th >Mean</th><th >Median</th></tr>`;
		$('#ind_apple_statics_table > thead').html(html_header);
		var html_tbody = '';
		$.each(data, function(index, value){  
			var label_and_val_max = format_metrics_lable_and_value(value.Metric , value.max)
			var label_and_val_min = format_metrics_lable_and_value(value.Metric , value.min)
			var label_and_val_mean = format_metrics_lable_and_value(value.Metric , value.mean)
			var label_and_val_median = format_metrics_lable_and_value(value.Metric , value.median)
			
			html_tbody += '<tr>';
			html_tbody += `<td>${label_and_val_max.lable}</td><td>${label_and_val_max.value}</td><td>${label_and_val_min.value}</td>
			<td>${label_and_val_mean.value}</td><td>${label_and_val_median.value}</td>`
			html_tbody += '</tr>';
		});
		$('#ind_apple_statics_table > tbody').html(html_tbody);
	}
	function update_fitbit_statics_table(data) {
		var html_header = `<tr><th>Metrics</th><th >Max</th><th >Min</th><th >Mean</th><th >Median</th></tr>`;
		$('#ind_fitbit_statics_table > thead').html(html_header);
		var html_tbody = '';
		$.each(data, function(index, value){  
			var label_and_val_max = format_metrics_lable_and_value(value.Metric , value.max)
			var label_and_val_min = format_metrics_lable_and_value(value.Metric , value.min)
			var label_and_val_mean = format_metrics_lable_and_value(value.Metric , value.mean)
			var label_and_val_median = format_metrics_lable_and_value(value.Metric , value.median)
			
			html_tbody += '<tr>';
			html_tbody += `<td>${label_and_val_max.lable}</td><td>${label_and_val_max.value}</td><td>${label_and_val_min.value}</td>
			<td>${label_and_val_mean.value}</td><td>${label_and_val_median.value}</td>`
			html_tbody += '</tr>';
		});
		$('#ind_fitbit_statics_table > tbody').html(html_tbody);
	}

	

	
	
	

	$('#device_select').on('change', function() {
		selected_device= this.value;
	});

	$('#cohort_select').on('change', function() {
		selected_cohort = this.value;
	});
	$('#age_select').on('change', function() {
		selected_age = this.value;
	});
	$('#gender_select').on('change', function() {
		selected_gender = this.value;
	});
	
	$('#filter_grp_data').on('click', function() {
		get_group_data()
	});

	$('#user_select').on('change', function() {
		selected_user= this.value;
		var user = user_nights.filter(x => x.ID == selected_user);
		picker.setHighlightedDays([  [moment(user[0].Start)  , moment(user[0].End)]  ])
	});

    picker.on('selected', (start_date, end_date) => {
		if (!selected_user){
			alert("Please Select User First Then Date !!")
			return false;
		}
        get_individual_data(start_date.dateInstance.toLocaleDateString(), 
            end_date.dateInstance.toLocaleDateString())				
    });


	$('#print_page').click(function(){
		window.print();
    });



})