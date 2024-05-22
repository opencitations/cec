$(document).ready(function(){
    var selectedModeGlobal = '';

    $('#classify-btn').click(function(){
        // Clear previous results
        $('#result').html('');
        $('#download-json-btn').hide();
        // Getting the selected mode
        var selectedMode = $("input[name='mode']:checked").val();
        selectedModeGlobal = selectedMode;
        var inputData = $('#input-text').val();
        $('#loading').show();
        $.ajax({
            url: conf["prefix"]+'classify',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 'sentences': inputData, 'mode': selectedMode }), // include the selected mode in the request
            success: function(response) {
                $('#loading').hide();
                var formattedHtml = formatResponse(response);
                $('#result').html(formattedHtml);
                    
                // Prepare the JSON data file for download
                var dataStr = JSON.stringify(response);
                var dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

                // Instead of showing the button directly, we attach the download event to it.
                $("#download-json-btn").off('click').on('click', function(event) {
                    var filename = selectedModeGlobal.replace(/ /g, "_") + "_prediction_results.json";
                    downloadJSON(dataUri, filename);
                }).show();
            }
        });
    });

    $('#upload-json-btn').click(function(){
        var fileInput = document.getElementById('json-file');
        var file = fileInput.files[0];

        if (!file) {
            alert("Please select a JSON file to upload.");
            return;
        }

        var formData = new FormData();
        formData.append("file", file);

        // Include selected_mode in formData
        var selectedMode = $("input[name='mode']:checked").val();
        formData.append("mode", selectedMode);

        $('#loading').show();

        $.ajax({
            url: conf["prefix"]+'upload_json',
            method: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function(response) {
                $('#loading').hide();
                var formattedHtml = formatResponse(response);
                $('#result').html(formattedHtml);

                // Prepare the JSON data file for download
                var dataStr = JSON.stringify(response);
                var dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

                $("#download-json-btn").off('click').on('click', function(event) {
                    var filename = "uploaded_json_results.json";
                    downloadJSON(dataUri, filename);
                }).show();
            },
            error: function(xhr, status, error) {
                $('#loading').hide();
                alert("An error occurred. Please check the format of your JSON and see if it is compliant with the instructions:" + error);
            }
        });
    });
});

function formatResponse(response) {
    // Define the order of the keys explicitly
    const keysOrder = [
        'SECTION',
        'CITATION',
        'SCIBERT MET POSITIVE PROBABILITY',
        'SCIBERT BKG POSITIVE PROBABILITY',
        'SCIBERT RES POSITIVE PROBABILITY',
        'XLNET MET POSITIVE PROBABILITY',
        'XLNET BKG POSITIVE PROBABILITY',
        'XLNET RES POSITIVE PROBABILITY',
        'MET ENSEMBLE CONFIDENCE',
        'BKG ENSEMBLE CONFIDENCE',
        'RES ENSEMBLE CONFIDENCE',
        'FINAL PREDICTION'
    ];

    // Start with an empty string
    var html = "";

    // Loop through each key in the response object
    for (var key in response) {
        if (response.hasOwnProperty(key)) {
            // Create a div for each sentence
            html += "<div class='result-block'><h3>Sentence: " + key + "</h3>";

            // Now loop through each attribute in the sentence result
            var sentenceData = response[key];
            
            // Loop through the keys based on the predefined order
            for (var i = 0; i < keysOrder.length; i++) {
                var attribute = keysOrder[i];
                if (sentenceData.hasOwnProperty(attribute)) {
                    // Add each attribute as a paragraph
                    html += "<p><strong>" + attribute + ":</strong> " + sentenceData[attribute] + "</p>";
                }
            }

            // Close the div
            html += "</div>";
        }
    }

    // Return the formatted HTML
    return html;
}

function downloadJSON(uri, filename) {
    var link = document.createElement("a");
    link.download = filename;
    link.href = uri;
    document.body.appendChild(link); // Needed for Firefox
    link.click();
    document.body.removeChild(link);
}
