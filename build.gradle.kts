plugins {
    id("java")
}

group = "com.rustport"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
    maven("https://repo.papermc.io/repository/maven-public/")
}

dependencies {
    compileOnly("io.papermc.paper:paper-api:26.2.build.112-stable")
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(25))
    }
}
