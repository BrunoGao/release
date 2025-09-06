/**
 * LJWX系统配置加载器 - JavaScript版本
 * 统一配置管理，支持YAML配置文件和环境变量覆盖
 * 
 * @author LJWX Team
 * @version 2.0.1
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

class LJWXConfigLoader {
    constructor(configPath = null) {
        this.configPath = configPath;
        this.config = null;
        this.loadConfig();
    }

    /**
     * 加载配置文件
     */
    loadConfig() {
        const possiblePaths = [
            '/app/config/ljwx-config.yaml',  // 容器内路径
            '/client/config/ljwx-config.yaml',  // 挂载路径
            path.join(__dirname, 'ljwx-config.yaml'),  // 同级目录
            'client/config/ljwx-config.yaml',  // 相对路径
            'config/ljwx-config.yaml',  // 简化路径
            this.configPath  // 指定路径
        ].filter(p => p);

        for (const configPath of possiblePaths) {
            if (fs.existsSync(configPath)) {
                try {
                    const fileContents = fs.readFileSync(configPath, 'utf8');
                    this.config = yaml.load(fileContents);
                    
                    // 应用环境变量覆盖
                    this.applyEnvOverrides();
                    return;
                } catch (error) {
                    // 继续尝试下一个路径
                    continue;
                }
            }
        }
        
        throw new Error('配置文件未找到，请确保ljwx-config.yaml存在');
    }

    /**
     * 应用环境变量覆盖
     */
    applyEnvOverrides() {
        // 数据库配置覆盖
        if (process.env.MYSQL_HOST) {
            this.config.database.mysql.host = process.env.MYSQL_HOST;
        }
        if (process.env.MYSQL_PORT) {
            this.config.database.mysql.port = parseInt(process.env.MYSQL_PORT);
        }
        if (process.env.MYSQL_DATABASE) {
            this.config.database.mysql.database = process.env.MYSQL_DATABASE;
        }
        if (process.env.MYSQL_USERNAME) {
            this.config.database.mysql.username = process.env.MYSQL_USERNAME;
        }
        if (process.env.MYSQL_PASSWORD) {
            this.config.database.mysql.password = process.env.MYSQL_PASSWORD;
        }

        if (process.env.REDIS_HOST) {
            this.config.database.redis.host = process.env.REDIS_HOST;
        }
        if (process.env.REDIS_PORT) {
            this.config.database.redis.port = parseInt(process.env.REDIS_PORT);
        }
        if (process.env.REDIS_PASSWORD) {
            this.config.database.redis.password = process.env.REDIS_PASSWORD;
        }

        // 服务端口覆盖
        if (process.env.SERVER_PORT && process.env.SERVICE_NAME) {
            const serviceName = process.env.SERVICE_NAME;
            if (this.config.services[serviceName]) {
                this.config.services[serviceName].port = parseInt(process.env.SERVER_PORT);
            }
        }
    }

    /**
     * 获取配置值，支持点号分隔的嵌套键
     * 
     * @param {string} key - 配置键，如 'database.mysql.host'
     * @param {any} defaultValue - 默认值
     * @returns {any} 配置值
     */
    get(key, defaultValue = null) {
        const keys = key.split('.');
        let value = this.config;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return defaultValue;
            }
        }

        return value;
    }

    /**
     * 获取数据库配置
     * 
     * @param {string} dbType - 数据库类型，如 'mysql', 'redis'
     * @returns {object} 数据库配置对象
     */
    getDatabaseConfig(dbType = 'mysql') {
        return this.get(`database.${dbType}`, {});
    }

    /**
     * 获取服务配置
     * 
     * @param {string} serviceName - 服务名称
     * @returns {object} 服务配置对象
     */
    getServiceConfig(serviceName) {
        return this.get(`services.${serviceName}`, {});
    }

    /**
     * 获取镜像配置
     * 
     * @returns {object} 镜像配置对象
     */
    getImageConfig() {
        return this.get('images', {});
    }

    /**
     * 获取数据库连接URL
     * 
     * @param {string} dbType - 数据库类型
     * @returns {string} 数据库连接URL
     */
    getDatabaseUrl(dbType = 'mysql') {
        const dbConfig = this.getDatabaseConfig(dbType);

        if (dbType === 'mysql') {
            const { host, port, database, username, password, charset = 'utf8mb4' } = dbConfig;
            return `mysql://${username}:${password}@${host}:${port}/${database}?charset=${charset}`;
        } else if (dbType === 'redis') {
            const { host, port, password = '', db = 0 } = dbConfig;
            const passwordPart = password ? `:${password}@` : '';
            return `redis://${passwordPart}${host}:${port}/${db}`;
        }

        return '';
    }

    /**
     * 重新加载配置
     */
    reload() {
        this.loadConfig();
    }
}

// 全局配置实例
let _configLoader = null;

/**
 * 获取全局配置实例
 * 
 * @returns {LJWXConfigLoader} 配置加载器实例
 */
function getConfig() {
    if (_configLoader === null) {
        _configLoader = new LJWXConfigLoader();
    }
    return _configLoader;
}

/**
 * 重新加载全局配置
 */
function reloadConfig() {
    if (_configLoader !== null) {
        _configLoader.reload();
    }
}

// 便捷函数
/**
 * 获取数据库配置
 */
function getDatabaseConfig(dbType = 'mysql') {
    return getConfig().getDatabaseConfig(dbType);
}

/**
 * 获取服务配置
 */
function getServiceConfig(serviceName) {
    return getConfig().getServiceConfig(serviceName);
}

/**
 * 获取数据库连接URL
 */
function getDatabaseUrl(dbType = 'mysql') {
    return getConfig().getDatabaseUrl(dbType);
}

module.exports = {
    LJWXConfigLoader,
    getConfig,
    reloadConfig,
    getDatabaseConfig,
    getServiceConfig,
    getDatabaseUrl
};

// 如果是直接运行此文件，进行测试
if (require.main === module) {
    try {
        const config = getConfig();
        
        console.log('=== LJWX配置测试 ===');
        console.log(`系统名称: ${config.get('system.name')}`);
        console.log(`系统版本: ${config.get('system.version')}`);
        console.log('');
        
        console.log('=== 数据库配置 ===');
        const mysqlConfig = getDatabaseConfig('mysql');
        console.log(`MySQL:`, mysqlConfig);
        console.log(`MySQL URL: ${getDatabaseUrl('mysql')}`);
        console.log('');
        
        const redisConfig = getDatabaseConfig('redis');
        console.log(`Redis:`, redisConfig);
        console.log(`Redis URL: ${getDatabaseUrl('redis')}`);
        console.log('');
        
        console.log('=== 服务配置 ===');
        ['ljwx-admin', 'ljwx-bigscreen', 'ljwx-boot'].forEach(service => {
            const serviceConfig = getServiceConfig(service);
            console.log(`${service}:`, serviceConfig);
        });
        console.log('');
        
        console.log('=== 镜像配置 ===');
        const imageConfig = config.getImageConfig();
        console.log(`镜像仓库: ${imageConfig.registry}`);
        console.log(`Admin镜像: ${imageConfig['ljwx-admin']}`);
        console.log(`Bigscreen镜像: ${imageConfig['ljwx-bigscreen']}`);
        console.log(`Boot镜像: ${imageConfig['ljwx-boot']}`);
        
    } catch (error) {
        console.error('配置加载测试失败:', error.message);
    }
}