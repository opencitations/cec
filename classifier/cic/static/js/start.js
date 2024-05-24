$('#demosent1').click(function(){
    $('#input-text').val($('#demosent1 .in-text-reference').html())
})

$('#demosent2').click(function(){
    $('#input-text').val($('#demosent2 .in-text-reference').html())
})

$('#demosent3').click(function(){
    $('#input-text').val($('#demosent3 .in-text-reference').html())
})


$(document).ready(function(){
    
    $('#result').hide();

    $('#classify-btn').click(function(){
        // Clear previous results
        $('#result').html('');
        $('#result').hide();

        var inputData = $('#input-text').val();
        var inputSection = $('#input-section').val();

        $('#loading').show();

        inputJSONRecord = `[('${inputSection.trim()}', "${inputData.trim()}")]`

        $.ajax({
            url: conf["prefix"]+'classify',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 'sentences': inputJSONRecord, 'mode': 'mixed' }), // include the selected mode in the request
            success: function(response) {
                $('#loading').hide();
                $('#result').removeClass('text-danger');
                $('#result').show();

                //console.log(response)

                var formattedHtml = formatCompactResponse(response);
                
                $('#result').html(formattedHtml);

                var details = formatResponse(response);

                $('#predictionDetailsContent').html(details);

                
                
            },
            error: function(xhr, status, error) {


                $('#loading').hide();
                $('#result').show();

                $('#result').addClass('text-danger');
                $('#result').html("An error occurred. Please check your input data.")                
            }
        });
    });
});

function formatCompactResponse(response) {
    prediction = response[0]['FINAL PREDICTION']   

    formattedHtml = `
    <div id='prediction'>
        <p id='predictionLabel'>${prediction}</p>
        <div id='predictionDetailsContainer'>
            <p id='predictionDetailsLink'>View details</p>
            <div id='predictionDetailsContent'>
            
            </div>
        </div>
    </di>`
    
    return formattedHtml;
}


function formatResponse(response) {
    // Define the order of the keys explicitly
    const keysOrder = [
        'CITATION',
        'SECTION',
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
            html += "<div class='result-block'>";

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