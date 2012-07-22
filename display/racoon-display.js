// based on http://mbostock.github.com/d3/ex/force.html
var width = 960, height = 500;
var color = d3.scale.category20();
var force = d3.layout.force()
			.charge(-120)
			.linkDistance(30)
			.size([width, height]);
var svg = d3.select("div#output").append("svg")
			.attr("width", width)
			.attr("height", height);

function displayRR() {
	var rresultURL = document.getElementById('rresult').value;
	
	d3.json(rresultURL, function(data) {

		var rresult = data;
		var nodes = [];
		var links = [];
		var groupcnt = 1;
		var nodecnt = 0;
		var from = 0;
		var to = 0;
		var locstr = "<h2>Crawl details</h2>";
	
		// build up the nodes list
		for(var location in rresult) {
			// add the location as a node:
			nodes.push({ "name": 'PAGE: ' + location, "group": groupcnt });
			
			var locationElement = document.createElement("div");
			locstr += '<h3>From <a href="' + location + '">' + location + '</a>:</h3>';
			
			// go through the nuggest from that location and add each as node:
			nuggets = rresult[location];
			for (var i = 0; i < nuggets.length; i++) {
				nodes.push({ "name": nuggets[i].URL, "group": groupcnt });
				locstr += '<div><a href="' + nuggets[i].URL + '">' + nuggets[i].text + '</a> (media type: ' + nuggets[i].type + ', size: ' + nuggets[i].size  + 'bytes)</div>';
			}
			groupcnt += 1;
		}
		
		locationElement.innerHTML = locstr;
		document.body.appendChild(locationElement);
		

		// build up the links list
		for(var location in rresult) {
			nuggets = rresult[location];
			from = nodecnt;
			for (var i = 0; i < nuggets.length; i++) {
				links.push({"source": from, "target": from + i + 1 , "value": 1});
				nodecnt += 1;
			}
			nodecnt += 1;
		}

		force.nodes(nodes)
			.links(links)
			.start();
		
		var link = svg.selectAll("line.link")
					.data(links)
					.enter().append("line")
					.attr("class", "link")
					.style("stroke-width", function(d) { return Math.sqrt(d.value); });
		
		var node = svg.selectAll("circle.node")
					.data(nodes)
					.enter().append("circle")
					.attr("class", "node")
					.attr("r", 5)
					.style("fill", function(d) { return color(d.group); })
					.call(force.drag);
		
		node.append("title")
			.text(function(d) { return d.name; });
		
		force.on("tick", function() {
			link.attr("x1", function(d) { return d.source.x; })
				.attr("y1", function(d) { return d.source.y; })
				.attr("x2", function(d) { return d.target.x; })
				.attr("y2", function(d) { return d.target.y; });
		
			node.attr("cx", function(d) { return d.x; })
				.attr("cy", function(d) { return d.y; });
		  });
	});
}