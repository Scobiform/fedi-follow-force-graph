    // This script is loaded when the graph page is opened
    // It initializes the graph with the user's followers and followings
    // and provides a function to filter nodes based on type
    
    var graphData;
    const container = document.getElementById('graph');
    const apiBaseUrl = '{{ api_base_url }}';
    const userJson = '{{ user | tojson | safe }}';  
    const userId = '{{ user.id | tojson | safe }}';
    const userAvatar = '{{ user.avatar }}';
    const userName = '{{ user.username | tojson | safe }}';
    const instance = '{{ instance }}';

    let avatarSizeMultiplier = 70;
    let textFontSize = 10.5;
    let instanceSizeMultiplier = 420;

    // Wait for the DOM to load before initializing the graph
    document.addEventListener('DOMContentLoaded', async function() {
        const elementResizeDetector = elementResizeDetectorMaker();
        try {

            // Fetch followers and followings
            const followers = await fetchAllItems(userId, 'followers', apiBaseUrl); 
            const followings = await fetchAllItems(userId, 'following', apiBaseUrl);
            // Generate graph data
            graphData = generateGraphData(userId, userName, userAvatar, followers, followings);
            // Calculate the number of connections for each node
            calculateNodeConnections(graphData.nodes, graphData.links);
            window.graph = initGraph(graphData);
            // Resize the graph when the window is resized
            elementResizeDetector.listenTo(document.getElementById('graph'), function(element) {
                    var width = element.clientWidth;
                    var height = element.clientHeight;
                    window.graph.width(width);
                    window.graph.height(height);
            });

            // Function to update the node size based on the slider value
            const slider = document.getElementById('nodeSizeSlider');
            const sliderValueDisplay = document.getElementById('sliderValue');

            slider.addEventListener('input', function() {
                const newSize = parseInt(this.value, 10);
                sliderValueDisplay.textContent = newSize;  // Update display
                console.log('New node size:', newSize);  // Debugging output

                if (window.graph && window.graph.graphData) {
                    window.graph.nodeRelSize(newSize);  // Update node size
                    window.graph.graphData(graphData);  // Reapply the graph data to update the graph
                }
            });
        }
        catch (error) {
            console.error('Initialization failed:', error); 
        }
    });

    // Function to fetch all items from an endpoint
    async function fetchAllItems(userId, endpoint, apiBaseUrl) {
        let items = [];

        let url = `${apiBaseUrl}/${endpoint}?user_id=${userId}`;
        
        const response = await fetch(url);

        const data = await response.json();
        console.log(`Received data length: ${data.length}`); // Debugging output

        // Add new items to the array
        items = items.concat(data);

        return items;
    }

    // Function to generate graph data from user, followers, and followings
    function generateGraphData(userId, userName, userAvatar, followers, followings) {
        const regex = /https?:\/\/([^/:]+)/; // Regex to extract domain from URL

        // Initialize user node with avatar and follower/following counts
        const nodes = [{
            id: userId,
            username: userName,
            type: 'user',
            avatar: userAvatar,
            followerCount: followers.length, // Assuming followers and followings are arrays
            followingCount: followings.length,
            instance: instance
        }];

        const instanceMap = new Map();

        // Function to create or get existing instance node
        function getInstanceNode(domain) {
            if (!instanceMap.has(domain)) {
                const instanceNode = {
                    id: `instance-${domain}`,
                    username: domain,
                    type: 'instance',
                    avatar: '', // Optional: a specific icon for instances
                    instance: domain
                };
                instanceMap.set(domain, instanceNode);
                nodes.push(instanceNode);
            }
            return instanceMap.get(domain);
        }

        // Generate nodes and links for followers
        const followerLinks = followers.map(f => {
            const domainMatch = f.url.match(regex);
            const domain = domainMatch ? domainMatch[1] : "unknown";
            const followerNode = {
                id: `follower-${f.id}`,
                username: f.username,
                type: 'follower',
                avatar: f.avatar,
                followerCount: f.followers_count,
                followingCount: f.following_count,
                instance: domain
        };
        nodes.push(followerNode);

            return { source: userId, target: followerNode.id, type: 'follow' };
        });

        // Generate nodes and links for followings
        const followingLinks = followings.map(f => {
            const domainMatch = f.url.match(regex);
            const domain = domainMatch ? domainMatch[1] : "unknown";
            const followingNode = {
                id: `following-${f.id}`,
                username: f.username,
                type: 'following',
                avatar: f.avatar,
                followerCount: f.followers_count,
                followingCount: f.following_count,
                instance: domain
            };
            nodes.push(followingNode);

            return { source: userId, target: followingNode.id, type: 'follow' };
        });

        // Generate instance links
        const instanceLinks = nodes.filter(n => n.type !== 'user').map(n => ({
            source: getInstanceNode(n.instance).id,
            target: n.id,
            type: 'instance'
        }));

        const links = followerLinks.concat(followingLinks, instanceLinks);

        console.log('Generated graph data:', { nodes, links }); // Debugging output
        return { nodes, links };
    }

    // Function to calculate the number of connections for each node
    function calculateNodeConnections(nodes, links) {
        const connectionCount = new Map();

        links.forEach(link => {
            const sourceId = (typeof link.source === 'object') ? link.source.id : link.source;
            const targetId = (typeof link.target === 'object') ? link.target.id : link.target;

            connectionCount.set(sourceId, (connectionCount.get(sourceId) || 0) + 1);
            connectionCount.set(targetId, (connectionCount.get(targetId) || 0) + 1);
        });

        nodes.forEach(node => {
            node.connectionCount = connectionCount.get(node.id) || 0;
        });
    }

    // Function to initialize the graph
    function initGraph(graphData) {
        // Initialize the graph
        const Graph = ForceGraph()(document.getElementById('graph'))
            .height(container.clientHeight)
            .graphData(graphData)
            .nodeAutoColorBy('type')
            .linkColor(link => {
                if (link.type === 'instance') return 'green';
                return 'rgba(0,0,0,0.5)';
            })
            .linkWidth(link => link.type === 'instance' ? 0.42 : 0.21)
            .nodeCanvasObject((node, ctx, globalScale) => {
                // Save the current state of the context
                ctx.save();
                const label = node.username;
                const fontSize = textFontSize / globalScale;
                let imgSize = node.type === 'instance' ? instanceSizeMultiplier + 7 * Math.sqrt(node.connectionCount) : avatarSizeMultiplier  + (Math.log(node.followerCount + 7) * 42);

                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                // Set the fill style based on the node type 
                ctx.fillStyle = node.type === 'instance' ? '#004225' : (node.type === 'follower' ? '#B28257' : '#00E074');

                // Draw a circle for all nodes
                ctx.beginPath();
                ctx.arc(node.x, node.y, imgSize / 2, 0, 2 * Math.PI);
                ctx.fill();

                // Draw circular avatars for non-instance nodes
                if (node.type !== 'instance' && node.avatar) {
                    if (!node.img) {
                        const img = new Image();
                        img.src = node.avatar;
                        img.onload = () => {
                            node.img = img;  // Cache the image in the node
                            drawAvatarCircle(ctx, node.x, node.y, imgSize / 2, img);
                        };
                    } else {
                        drawAvatarCircle(ctx, node.x, node.y, imgSize / 2, node.img);
                    }
                }

                // Set the text color only white for instance nodes
                ctx.fillStyle = node.type === 'instance' ? '#F9F5F1' : ctx.fillStyle;
                ctx.fillText(label, node.x, node.y);

                ctx.restore();
            })
        // Show node info on click
        .onNodeClick((node, color) => {
            console.log(node);
            // Open the user's profile in a new tab
            if (node.type === 'follower' || node.type === 'following') {
                // Open the user's profile in a new tab @username@instance
                window.open(`https://${instance}/@${node.username}@${node.instance}`, '_blank');
            }
        })
        // Paint the node pointer area with a circle
        .nodePointerAreaPaint((node, color, ctx) => {
            // Determine the size of the node based on type and attributes
            const imgSize = node.type === 'instance' ? instanceSizeMultiplier
                             + 7 * Math.sqrt(node.connectionCount) : avatarSizeMultiplier
                             + (Math.log(node.followerCount + 7) * 7
            );
            ctx.fillStyle = color;
            // Draw a circle for the hit area, which matches the visual representation of the node
            ctx.beginPath();
            ctx.arc(node.x, node.y, imgSize / 2, 0, 2 * Math.PI, false);
            ctx.fill();
        })
        // Pop-up node info on hover
        .onNodeHover(node => {
            container.style.cursor = node ? 'pointer' : null;
        })
        // Show node info on hover
        .onNodeHover(node => {
            if (node) {
                console.log(node);
            }
        })
        .onNodeDragEnd(node => {
            //node.fx = node.x;
            //node.fy = node.y;
        })
        ;

        // # Add forces to the graph
        // Dynamic collision radius based on node type
        Graph.d3Force('collide', d3.forceCollide().radius(node => node.type === 'instance' ? 60 : 42))
            // Increased repulsive force
            .d3Force('charge', d3.forceManyBody().strength(-42000)) 
            // Increased distance and adjusted strength for links 
            .d3Force('link', d3.forceLink().id(d => d.id).distance(200).strength(0.5))
            .d3Force('x', d3.forceX(container.clientWidth / 2).strength(0.05))
            .d3Force('y', d3.forceY(container.clientHeight / 2).strength(0.05))
            .d3Force('center', d3.forceCenter(container.clientWidth / 2, container.clientHeight / 2))
            // Link distance based on type
            .d3Force('link', d3.forceLink().distance(link => link.type === 'instance' ? 200 : 100).strength(0.5));

        return Graph;
    }

    // Function to draw an avatar circle
    function drawAvatarCircle(ctx, x, y, radius, img) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.clip();  // Clip to the circle
        ctx.drawImage(img, x - radius, y - radius, radius * 2, radius * 2);
        ctx.restore();  // Restore to the original state to draw text or other shapes later
    }

    // Function to filter nodes based on type    
    window.filterNodes = function(filterType) {
        // This will hold the IDs of nodes that should be visible based on the filtering criteria.
        const visibleNodes = new Set();

        // Add directly visible nodes based on filter type.
        graphData.nodes.forEach(node => {
            if (filterType === 'all' || node.type === filterType || node.type === 'user') {
                visibleNodes.add(node.id);
            }
        });

        // Filter links based on visible nodes.
        const filteredLinks = graphData.links.filter(link => {
            let sourceId = (typeof link.source === 'object') ? link.source.id : link.source;
            let targetId = (typeof link.target === 'object') ? link.target.id : link.target;
            return visibleNodes.has(sourceId) && visibleNodes.has(targetId);
        });

        // Ensure instance nodes linked to any visible node are also shown
        filteredLinks.forEach(link => {
            let sourceId = (typeof link.source === 'object') ? link.source.id : link.source;
            let targetId = (typeof link.target === 'object') ? link.target.id : link.target;
            visibleNodes.add(sourceId);
            visibleNodes.add(targetId);
        });

        // Prepare the filtered data for nodes and links.
        const filteredData = {
            nodes: graphData.nodes.filter(node => visibleNodes.has(node.id)),
            links: filteredLinks
        };

        // Update the graph with the filtered data.
        graph.graphData(filteredData);
    }

    // Function to update graph values based on the slider
    document.addEventListener('DOMContentLoaded', function() {

        const slider = document.getElementById('nodeSizeSlider');
        const sliderValueDisplay = document.getElementById('sliderValue');

        const textSlider = document.getElementById('textFontSizeSlider');
        const textSliderValueDisplay = document.getElementById('textSliderValue');

        const instanceSlider = document.getElementById('instanceSizeSlider');
        const instanceSliderValueDisplay = document.getElementById('instanceSliderValue');

        slider.addEventListener('input', function() {
            avatarSizeMultiplier = parseInt(this.value, 10); 
            sliderValueDisplay.textContent = avatarSizeMultiplier; 

            // Reapply the graph data to update the graph
            if (window.graph && window.graph.graphData) {
                window.graph.graphData(graphData); 
            }
        });

        textSlider.addEventListener('input', function() {
            textFontSize = parseInt(this.value, 10); 
            textSliderValueDisplay.textContent = textFontSize; 

            // Reapply the graph data to update the graph
            if (window.graph && window.graph.graphData) {
                window.graph.graphData(graphData); 
            }
        });

        if (instanceSlider){
            instanceSlider.addEventListener('input', function() {
                instanceSizeMultiplier = parseInt(this.value, 10); 
                instanceSliderValueDisplay.textContent = instanceSizeMultiplier; 

                // Reapply the graph data to update the graph
                if (window.graph && window.graph.graphData) {
                    window.graph.graphData(graphData); 
                }
            });
        }

    });