var request = new XMLHttpRequest();
request.open("GET", "./static/trade_links.json", false);
request.send(null);
var data = JSON.parse(request.responseText);

const time_formatter = new Intl.RelativeTimeFormat('en', { 
    numeric: 'auto',
    style: 'long',
    localeMatcher: 'best fit'
});
function time_diff(timestamp){
    const minutes = (new Date(timestamp + "Z") - new Date(Date.now())) / 60000
    if (Math.abs(minutes) < 60){
        return time_formatter.format(Math.round(minutes), 'minute');
    }
    const hours = minutes / 60
    if (Math.abs(hours) < 24){
        return time_formatter.format(Math.round(hours), 'hour')
    }
    const days = hours / 24
    return  time_formatter.format(Math.round(days), 'day');

}

document.getElementById('generic_link').href = data["generic_link"];
document.getElementById('mana_link').href = data["mana_link"];
document.getElementById('last_update').innerHTML = time_diff(data["time_since_last_update"]);
