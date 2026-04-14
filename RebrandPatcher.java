import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Enumeration;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassVisitor;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.MethodVisitor;
import jdk.internal.org.objectweb.asm.Opcodes;

public class RebrandPatcher {
    private static final String TARGET_VERSION_NAME = "Sloxy (SloBlock Proxy)";
    private static final String PLAIN_PREFIX = "[SloBlock Proxy] ";
    private static final String[] STARTUP_LINES = new String[] {
            " ",
            "§x§a§d§1§5§e§d░██████╗██╗░░░░░░█████╗░██╗░░██╗██╗░░░██╗",
            "§x§a§d§1§5§e§d██╔════╝██║░░░░░██╔══██╗╚██╗██╔╝╚██╗░██╔╝",
            "§x§a§d§1§5§e§d╚█████╗░██║░░░░░██║░░██║░╚███╔╝░░╚████╔╝░",
            "§x§3§3§e§0§f§f░╚═══██╗██║░░░░░██║░░██║░██╔██╗░░░╚██╔╝░░",
            "§x§3§3§e§0§f§f██████╔╝███████╗╚█████╔╝██╔╝╚██╗░░░██║░░░",
            "§x§3§3§e§0§f§f╚═════╝░╚══════╝░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░",
            " ",
            "§fProxy started §8(§5Slo§bxy§8)",
            " "
    };

    public static void main(String[] args) throws Exception {
        Path root = Path.of("C:\\Users\\majko\\Documents\\PROJECTS\\Server Jars\\Sloxy");
        Path input = root.resolve("FlameCord.jar");
        Path output = root.resolve("server.jar");
        Path temp = root.resolve("server.jar.tmp");

        try (JarFile jar = new JarFile(input.toFile());
             JarOutputStream jos = new JarOutputStream(Files.newOutputStream(temp))) {
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                byte[] data;
                try (InputStream is = jar.getInputStream(entry)) {
                    data = is.readAllBytes();
                }

                if (entry.getName().endsWith(".class")) {
                    data = transformClass(entry.getName(), data);
                }

                JarEntry outEntry = new JarEntry(entry.getName());
                outEntry.setTime(entry.getTime());
                jos.putNextEntry(outEntry);
                jos.write(data);
                jos.closeEntry();
            }
        }

        Files.move(temp, output, StandardCopyOption.REPLACE_EXISTING);
        System.out.println("Patched jar written to: " + output);
    }

    private static byte[] transformClass(String className, byte[] bytes) {
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS);
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM8, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);

                if ("net/md_5/bungee/BungeeCordLauncher.class".equals(className)
                        && "main".equals(name)
                        && "([Ljava/lang/String;)V".equals(descriptor)) {
                    return new LauncherMainVisitor(new GenericStringVisitor(mv, className, name));
                }

                if ("net/md_5/bungee/connection/DownstreamBridge.class".equals(className)
                        && "handle".equals(name)
                        && "(Lnet/md_5/bungee/protocol/packet/PluginMessage;)V".equals(descriptor)) {
                    return new DownstreamBrandVisitor(new GenericStringVisitor(mv, className, name));
                }

                if ("net/md_5/bungee/connection/InitialHandler.class".equals(className)
                        && "handle".equals(name)
                        && "(Lnet/md_5/bungee/protocol/packet/StatusRequest;)V".equals(descriptor)) {
                    return new InitialHandlerStatusVisitor(new GenericStringVisitor(mv, className, name));
                }

                if ("dev/_2lstudios/flamecord/antibot/LoggerWrapper.class".equals(className)
                        && "log".equals(name)
                        && "(Ljava/util/logging/Level;Ljava/lang/String;[Ljava/lang/Object;)V".equals(descriptor)) {
                    return new LoggerWrapperPrefixVisitor(new GenericStringVisitor(mv, className, name));
                }

                return new GenericStringVisitor(mv, className, name);
            }
        };

        cr.accept(cv, 0);
        return cw.toByteArray();
    }

    private static class GenericStringVisitor extends MethodVisitor {
        private final String className;
        private final String methodName;

        GenericStringVisitor(MethodVisitor mv, String className, String methodName) {
            super(Opcodes.ASM8, mv);
            this.className = className;
            this.methodName = methodName;
        }

        @Override
        public void visitLdcInsn(Object value) {
            if (value instanceof String s) {
                String updated = s;

                if ("dev/_2lstudios/flamecord/commands/FlameCordCommand.class".equals(className)
                        && "<init>".equals(methodName)
                        && "flamecord".equals(updated)) {
                    updated = "sloxy";
                }

                // Display/config-only replacements without touching internal owner paths.
                updated = updated.replace("[FlameCord]", "[Sloxy]");
                updated = updated.replace("/flamecord", "/sloxy");
                updated = updated.replace("flamecord.yml", "sloxy.yml");
                updated = updated.replace("./flamecord", "./sloxy");
                updated = updated.replace("§8[§5Slo§bxy§8] §r", PLAIN_PREFIX);
                updated = updated.replace("§8[§5Slo§bxy§8]", PLAIN_PREFIX);
                updated = updated.replace("§7[§cSloxy§7] ", PLAIN_PREFIX);
                updated = updated.replace("§7[§cSloxy§7]", PLAIN_PREFIX);
                updated = updated.replace("§c[Sloxy] ", PLAIN_PREFIX);
                updated = updated.replace("§c[Sloxy]", PLAIN_PREFIX);
                updated = updated.replace("§4[Sloxy] ", PLAIN_PREFIX);
                updated = updated.replace("§4[Sloxy]", PLAIN_PREFIX);
                updated = updated.replace("[Sloxy] ", PLAIN_PREFIX);
                updated = updated.replace("[Sloxy]", PLAIN_PREFIX);
                if (!updated.contains("/")) {
                    updated = updated.replace("FlameCord", "Sloxy");
                }

                value = updated;
            }
            super.visitLdcInsn(value);
        }
    }

    private static final class LoggerWrapperPrefixVisitor extends MethodVisitor {
        LoggerWrapperPrefixVisitor(MethodVisitor mv) {
            super(Opcodes.ASM8, mv);
        }

        @Override
        public void visitFieldInsn(int opcode, String owner, String name, String descriptor) {
            if (opcode == Opcodes.GETSTATIC
                    && "net/md_5/bungee/api/ChatColor".equals(owner)) {
                // Strip colorized prefix pieces; keep message body untouched.
                super.visitLdcInsn("");
                return;
            }
            super.visitFieldInsn(opcode, owner, name, descriptor);
        }

        @Override
        public void visitLdcInsn(Object value) {
            if (value instanceof String s) {
                if ("FlameCord".equals(s)
                        || "Sloxy".equals(s)
                        || "[Sloxy]".equals(s)
                        || "[Sloxy] ".equals(s)) {
                    value = PLAIN_PREFIX;
                } else if ("[".equals(s)
                        || "[ ".equals(s)
                        || "]".equals(s)
                        || "] ".equals(s)) {
                    value = "";
                }
            }
            super.visitLdcInsn(value);
        }
    }

    private static final class DownstreamBrandVisitor extends MethodVisitor {
        private int replaced;

        DownstreamBrandVisitor(MethodVisitor mv) {
            super(Opcodes.ASM8, mv);
        }

        @Override
        public void visitMethodInsn(int opcode, String owner, String name, String descriptor, boolean isInterface) {
            if (replaced < 2
                    && opcode == Opcodes.INVOKESTATIC
                    && "net/md_5/bungee/protocol/DefinedPacket".equals(owner)
                    && "writeString".equals(name)
                    && "(Ljava/lang/String;Lio/netty/buffer/ByteBuf;)V".equals(descriptor)) {
                // Stack before call: ..., originalString, byteBuf
                super.visitInsn(Opcodes.SWAP);
                super.visitInsn(Opcodes.POP);
                super.visitLdcInsn(TARGET_VERSION_NAME);
                super.visitInsn(Opcodes.SWAP);
                replaced++;
            } else if (replaced < 2
                    && opcode == Opcodes.INVOKEVIRTUAL
                    && "java/lang/String".equals(owner)
                    && "getBytes".equals(name)
                    && "(Ljava/nio/charset/Charset;)[B".equals(descriptor)) {
                // Stack before call: ..., originalString, charset
                super.visitInsn(Opcodes.SWAP);
                super.visitInsn(Opcodes.POP);
                super.visitLdcInsn(TARGET_VERSION_NAME);
                super.visitInsn(Opcodes.SWAP);
                replaced++;
            }
            super.visitMethodInsn(opcode, owner, name, descriptor, isInterface);
        }
    }

    private static final class InitialHandlerStatusVisitor extends MethodVisitor {
        InitialHandlerStatusVisitor(MethodVisitor mv) {
            super(Opcodes.ASM8, mv);
        }

        @Override
        public void visitMethodInsn(int opcode, String owner, String name, String descriptor, boolean isInterface) {
            if (opcode == Opcodes.INVOKESPECIAL
                    && "net/md_5/bungee/api/ServerPing$Protocol".equals(owner)
                    && "<init>".equals(name)
                    && "(Ljava/lang/String;I)V".equals(descriptor)) {
                // Replace only the display name arg, keep protocolVersion int untouched.
                super.visitInsn(Opcodes.SWAP);
                super.visitInsn(Opcodes.POP);
                super.visitLdcInsn(TARGET_VERSION_NAME);
                super.visitInsn(Opcodes.SWAP);
            }
            super.visitMethodInsn(opcode, owner, name, descriptor, isInterface);
        }
    }

    private static final class LauncherMainVisitor extends MethodVisitor {
        private boolean injectedStartup = false;

        LauncherMainVisitor(MethodVisitor mv) {
            super(Opcodes.ASM8, mv);
        }

        @Override
        public void visitMethodInsn(int opcode, String owner, String name, String descriptor, boolean isInterface) {
            if (!injectedStartup
                    && opcode == Opcodes.INVOKEVIRTUAL
                    && "java/util/logging/Logger".equals(owner)
                    && "info".equals(name)
                    && "(Ljava/lang/String;)V".equals(descriptor)) {
                // Remove the old startup banner lines.
                super.visitInsn(Opcodes.POP2);
                return;
            }

            if (!injectedStartup
                    && opcode == Opcodes.INVOKEVIRTUAL
                    && "net/md_5/bungee/BungeeCord".equals(owner)
                    && "start".equals(name)
                    && "()V".equals(descriptor)) {
                // Keep only the final requested startup block.
                for (String line : STARTUP_LINES) {
                    super.visitVarInsn(Opcodes.ALOAD, 3);
                    super.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "net/md_5/bungee/BungeeCord", "getLogger", "()Ljava/util/logging/Logger;", false);
                    super.visitLdcInsn(line);
                    super.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/util/logging/Logger", "info", "(Ljava/lang/String;)V", false);
                }

                injectedStartup = true;
            }

            super.visitMethodInsn(opcode, owner, name, descriptor, isInterface);
        }
    }
}
