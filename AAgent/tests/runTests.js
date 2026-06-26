/**
 * 测试运行器 - 执行所有单元测试
 * 运行命令: node tests/runTests.js
 */

console.log('\n' + '='.repeat(60));
console.log('🧪 AI圆桌讨论系统 - TDD测试套件');
console.log('='.repeat(60));

const tests = [
    {
        name: '专家Persona生成',
        file: './unit/expertPersona.test.js',
        description: '测试专家角色生成和SystemPrompt构建'
    },
    {
        name: '讨论流程控制',
        file: './unit/discussionFlow.test.js',
        description: '测试讨论轮次规划和状态管理'
    },
    {
        name: '共识与分歧提取',
        file: './unit/consensusExtraction.test.js',
        description: '测试共识关键词提取和分歧检测算法'
    }
];

console.log('\n📋 测试计划:\n');
tests.forEach((test, index) => {
    console.log(`${index + 1}. ${test.name}`);
    console.log(`   文件: ${test.file}`);
    console.log(`   说明: ${test.description}\n`);
});

console.log('='.repeat(60));
console.log('ℹ️  注意: 当前测试文件中的断言已注释，待实现代码后取消注释');
console.log('='.repeat(60));

// 提示如何运行测试
console.log('\n📖 运行指南:\n');
console.log('1. 实现对应的服务代码');
console.log('2. 在测试文件中取消注释相关断言');
console.log('3. 运行单个测试:');
console.log('   node tests/unit/expertPersona.test.js');
console.log('   node tests/unit/discussionFlow.test.js');
console.log('   node tests/unit/consensusExtraction.test.js\n');
console.log('4. 或使用npm脚本:');
console.log('   npm test\n');

console.log('='.repeat(60));
console.log('✅ 测试框架已就绪！');
console.log('='.repeat(60) + '\n');
