#!/bin/bash
# Test Google Transit Search API

echo "=== Testing Google Transit Search API ==="

echo -e "\nTest 1: GET request with query parameters"
docker exec vps_project-web-1 php /usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/api/google_transit_search.php <<EOF
<?php
\$_SERVER['REQUEST_METHOD'] = 'GET';
\$_GET['origin'] = '東京駅';
\$_GET['destination'] = '渋谷駅';
require('/usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/api/google_transit_search.php');
EOF

echo -e "\n\nTest 2: POST request with JSON"
echo '{"origin":"新宿駅","destination":"品川駅"}' | docker exec -i vps_project-web-1 php -r '
$_SERVER["REQUEST_METHOD"] = "POST";
$input = stream_get_contents(STDIN);
$GLOBALS["php_input"] = $input;
stream_wrapper_unregister("php");
stream_wrapper_register("php", "MockPhpStream");
MockPhpStream::$data = $input;
require("/usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/api/google_transit_search.php");

class MockPhpStream {
    public static $data = "";
    private $position = 0;
    
    public function stream_open($path, $mode, $options, &$opened_path) { return true; }
    
    public function stream_read($count) {
        $ret = substr(self::$data, $this->position, $count);
        $this->position += strlen($ret);
        return $ret;
    }
    
    public function stream_eof() { return $this->position >= strlen(self::$data); }
    public function stream_stat() { return []; }
}'

echo -e "\n\nTest 3: Direct command line test"
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py "東京タワー" "スカイツリー"