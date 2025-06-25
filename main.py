import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisShardInfo;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import java.io.File;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.security.KeyStore;
import java.util.Objects;

public class RedisSeeder {

    public static void main(String[] args) throws Exception {
        // Caminho para o truststore JKS gerado a partir do ca.crt
        String trustStorePath = "src/main/resources/certs/ca.jks";
        String trustStorePassword = "changeit";

        // Inicializa contexto SSL
        KeyStore trustStore = KeyStore.getInstance("JKS");
        trustStore.load(new FileInputStream(trustStorePath), trustStorePassword.toCharArray());

        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(trustStore);

        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(null, tmf.getTrustManagers(), null);

        // Conexão com Redis via TLS
        JedisShardInfo shardInfo = new JedisShardInfo("localhost", 6380, true);
        shardInfo.setPassword("12345678");
        shardInfo.setSslSocketFactory(sslContext.getSocketFactory());

        try (Jedis jedis = new Jedis(shardInfo)) {
            System.out.println("🔐 Conectado ao Redis via SSL");

            ObjectMapper mapper = new ObjectMapper();
            File dir = new File("src/main/resources/json");

            for (File file : Objects.requireNonNull(dir.listFiles((d, name) -> name.endsWith(".json")))) {
                String content = Files.readString(file.toPath());
                JsonNode root = mapper.readTree(content);

                if (root.isArray()) {
                    for (JsonNode node : root) {
                        JsonNode keyNode = node.get("id_eq3_contratante");
                        if (keyNode != null) {
                            String key = keyNode.asText();
                            jedis.rpush(key, mapper.writeValueAsString(node));
                            System.out.println("✅ Inserido no Redis (SSL): " + key);
                        } else {
                            System.err.println("⚠️ Campo 'id_eq3_contratante' ausente em: " + file.getName());
                        }
                    }
                } else {
                    System.err.println("⚠️ JSON não é um array: " + file.getName());
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }


version: '3.8'
services:
  redis:
    image: redis:7.2
    container_name: redis-mock
    ports:
      - "6379:6379"
      - "6380:6380"  # Porta TLS
    command:
      - redis-server
      - --tls-port 6380
      - --port 0
      - --tls-cert-file /certs/redis.crt
      - --tls-key-file /certs/redis.key
      - --tls-ca-cert-file /certs/ca.crt
      - --requirepass "12345678"
    volumes:
      - ./certs:/certs
      - redis-data:/data

volumes:
  redis-data:
    }
}
